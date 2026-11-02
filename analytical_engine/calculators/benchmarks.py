"""
Benchmarking Engine — Layer 2 Analytical Engine
-------------------------------------------------
Aggregates per-event analytics into statistical benchmark reports
across dimensions: task_type, model, provider, department, and time.

All aggregation is done in Python over pre-computed EventAnalytics objects
to keep logic independent of the DB layer. The main.py endpoints are
responsible for fetching events and calling compute_energy/compute_carbon
before passing results here.
"""

from __future__ import annotations
from collections import defaultdict
from datetime import datetime
from typing import Optional

from ..schemas.schema import (
    BenchmarkReport,
    ModelRanking,
    ProviderComparison,
    DepartmentAttribution,
    CarbonTrendPoint,
    EventAnalytics,
)


def _safe_percentile(values: list[float], pct: float) -> float:
    """
    Compute a percentile from a sorted list without numpy.
    pct should be in [0, 100].
    """
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    k = (pct / 100) * (n - 1)
    lo, hi = int(k), min(int(k) + 1, n - 1)
    frac = k - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def _safe_avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _safe_opt_avg(values: list[float]) -> Optional[float]:
    return round(sum(values) / len(values), 6) if values else None


# ---------------------------------------------------------------------------
# Task-type benchmarks
# ---------------------------------------------------------------------------

def compute_benchmark_report(analytics: list[EventAnalytics]) -> list[BenchmarkReport]:
    """
    Group EventAnalytics by task_type and compute aggregate energy/carbon stats.

    Returns a list of BenchmarkReport, one per unique task_type.
    """
    groups: dict[str, list[EventAnalytics]] = defaultdict(list)
    for ev in analytics:
        key = ev.task_type or "unknown"
        groups[key].append(ev)

    reports: list[BenchmarkReport] = []
    for task_type, events in groups.items():
        energy_vals = [e.energy.energy_kwh for e in events]
        carbon_vals = [e.carbon.total_gco2eq for e in events]
        tokens_per_kwh_vals = [e.tokens_per_kwh for e in events if e.tokens_per_kwh is not None]
        gco2_per_1k_vals = [e.gco2eq_per_1k_tokens for e in events if e.gco2eq_per_1k_tokens is not None]

        reports.append(BenchmarkReport(
            task_type=task_type,
            event_count=len(events),
            avg_energy_kwh=round(_safe_avg(energy_vals), 8),
            min_energy_kwh=round(min(energy_vals, default=0.0), 8),
            max_energy_kwh=round(max(energy_vals, default=0.0), 8),
            p50_energy_kwh=round(_safe_percentile(energy_vals, 50), 8),
            p95_energy_kwh=round(_safe_percentile(energy_vals, 95), 8),
            total_energy_kwh=round(sum(energy_vals), 8),
            avg_carbon_gco2eq=round(_safe_avg(carbon_vals), 6),
            total_carbon_gco2eq=round(sum(carbon_vals), 6),
            avg_tokens_per_kwh=_safe_opt_avg(tokens_per_kwh_vals),
            avg_gco2eq_per_1k_tokens=_safe_opt_avg(gco2_per_1k_vals),
        ))

    return sorted(reports, key=lambda r: r.total_energy_kwh, reverse=True)


# ---------------------------------------------------------------------------
# Model rankings
# ---------------------------------------------------------------------------

def compute_model_rankings(analytics: list[EventAnalytics]) -> list[ModelRanking]:
    """
    Group EventAnalytics by model_name and compute efficiency rankings.

    Models are sorted ascending by avg_carbon_gco2eq
    (most carbon-efficient model first).
    """
    groups: dict[str, list[EventAnalytics]] = defaultdict(list)
    for ev in analytics:
        groups[ev.model_name].append(ev)

    rankings: list[ModelRanking] = []
    for model_name, events in groups.items():
        energy_vals = [e.energy.energy_kwh for e in events]
        carbon_vals = [e.carbon.total_gco2eq for e in events]
        tokens_per_kwh_vals = [e.tokens_per_kwh for e in events if e.tokens_per_kwh is not None]
        gco2_per_1k_vals = [e.gco2eq_per_1k_tokens for e in events if e.gco2eq_per_1k_tokens is not None]

        # Use first non-None provider for display
        provider = next((e.provider for e in events if e.provider), None)

        rankings.append(ModelRanking(
            model_name=model_name,
            event_count=len(events),
            total_energy_kwh=round(sum(energy_vals), 8),
            avg_energy_kwh=round(_safe_avg(energy_vals), 8),
            total_carbon_gco2eq=round(sum(carbon_vals), 6),
            avg_carbon_gco2eq=round(_safe_avg(carbon_vals), 6),
            avg_tokens_per_kwh=_safe_opt_avg(tokens_per_kwh_vals),
            avg_gco2eq_per_1k_tokens=_safe_opt_avg(gco2_per_1k_vals),
            provider=provider,
        ))

    return sorted(rankings, key=lambda r: r.avg_carbon_gco2eq)


# ---------------------------------------------------------------------------
# Provider comparison
# ---------------------------------------------------------------------------

def compute_provider_comparison(analytics: list[EventAnalytics]) -> list[ProviderComparison]:
    """
    Group EventAnalytics by provider (gemini, ollama, etc.) and compare metrics.
    """
    groups: dict[str, list[EventAnalytics]] = defaultdict(list)
    for ev in analytics:
        key = ev.provider or "unknown"
        groups[key].append(ev)

    comparisons: list[ProviderComparison] = []
    for provider, events in groups.items():
        energy_vals = [e.energy.energy_kwh for e in events]
        carbon_vals = [e.carbon.total_gco2eq for e in events]
        tokens_per_kwh_vals = [e.tokens_per_kwh for e in events if e.tokens_per_kwh is not None]

        comparisons.append(ProviderComparison(
            provider=provider,
            event_count=len(events),
            total_energy_kwh=round(sum(energy_vals), 8),
            avg_energy_kwh=round(_safe_avg(energy_vals), 8),
            total_carbon_gco2eq=round(sum(carbon_vals), 6),
            avg_carbon_gco2eq=round(_safe_avg(carbon_vals), 6),
            avg_tokens_per_kwh=_safe_opt_avg(tokens_per_kwh_vals),
        ))

    return sorted(comparisons, key=lambda c: c.avg_carbon_gco2eq)


# ---------------------------------------------------------------------------
# Department attribution
# ---------------------------------------------------------------------------

def compute_department_attribution(analytics: list[EventAnalytics]) -> list[DepartmentAttribution]:
    """
    Group EventAnalytics by department for ESG cost-center carbon attribution.
    Computes each department's share of total platform carbon footprint.
    """
    groups: dict[str, list[EventAnalytics]] = defaultdict(list)
    for ev in analytics:
        key = ev.department or "unattributed"
        groups[key].append(ev)

    # Total platform carbon (for share %)
    total_carbon = sum(e.carbon.total_gco2eq for e in analytics)

    attributions: list[DepartmentAttribution] = []
    for dept, events in groups.items():
        energy_vals = [e.energy.energy_kwh for e in events]
        carbon_vals = [e.carbon.total_gco2eq for e in events]
        cost_vals = [e.cost_usd for e in events if e.cost_usd is not None]
        dept_total_carbon = sum(carbon_vals)

        attributions.append(DepartmentAttribution(
            department=dept,
            event_count=len(events),
            total_energy_kwh=round(sum(energy_vals), 8),
            total_carbon_gco2eq=round(dept_total_carbon, 6),
            total_cost_usd=round(sum(cost_vals), 4) if cost_vals else None,
            avg_carbon_per_event_gco2eq=round(_safe_avg(carbon_vals), 6),
            carbon_share_pct=round(
                (dept_total_carbon / total_carbon * 100), 2
            ) if total_carbon > 0 else 0.0,
        ))

    return sorted(attributions, key=lambda d: d.total_carbon_gco2eq, reverse=True)


# ---------------------------------------------------------------------------
# Carbon intensity trend
# ---------------------------------------------------------------------------

def compute_carbon_trend(analytics: list[EventAnalytics]) -> list[CarbonTrendPoint]:
    """
    Extract a time-ordered carbon intensity series from EventAnalytics.
    Useful for identifying when greener grid windows occur.
    """
    points: list[CarbonTrendPoint] = []
    for ev in analytics:
        points.append(CarbonTrendPoint(
            timestamp=ev.timestamp,
            region=None,   # region not stored in EventAnalytics; enriched by main.py
            carbon_intensity_gco2_per_kwh=ev.carbon.carbon_intensity_gco2_per_kwh,
            event_id=ev.event_id,
            model_name=ev.model_name,
        ))
    # Return sorted by timestamp ascending
    return sorted(points, key=lambda p: p.timestamp)
