# Calculation Boundaries and Methodology

## Principles

All formulas are versioned. A result records its formula version, input identifiers, units, evidence class, coverage and assumptions. The analytics engine must return `unknown` when the inputs required by a calculation are unavailable; it may return an estimate only under an approved, documented estimation model.

## Core definitions

Use SI units internally: joules (J), watt-hours (Wh), kilowatt-hours (kWh), grams CO2e (gCO2e), seconds, and token counts. UI conversion is presentation-only.

| Metric | Formula / rule | Boundary |
| --- | --- | --- |
| Energy | `E_Wh = integral(power_W over time) / 3600` when sampled power is available. | Measured only when meter/telemetry coverage and sampling quality are recorded. |
| Energy from start/end readings | `E_Wh = end_Wh - start_Wh`. | Reject/flag negative or incomplete readings. |
| Estimated energy | `E_est_Wh = approved_estimation_model(inputs)`. | The model, calibration data, applicability and uncertainty are TBD. |
| Carbon emissions | `C_gCO2e = E_kWh × CI_gCO2e_per_kWh`. | Requires energy plus an intensity value compatible with region/time. |
| Energy/request | `sum(E for included execution boundary) / count(included requests)`. | State whether host-only, accelerator-only, or total attributable energy is included. |
| Carbon/request | `sum(C for included execution boundary) / count(included requests)`. | Do not aggregate mixed intensity scopes without disclosure. |
| Energy/1,000 tokens | `1000 × E_Wh / (input_tokens + output_tokens)`. | Undefined when total known tokens is zero or absent. |
| Carbon/1,000 tokens | `1000 × C_gCO2e / (input_tokens + output_tokens)`. | Same token coverage requirement. |

## Attribution and system boundary

The calculation record must declare its boundary: `accelerator`, `host_compute`, `controlled_machine`, `provider_reported`, or `workload_estimate` (names provisional). The initial default should not claim facility-wide energy, cooling overhead, network energy, embodied carbon, or shared-resource allocation unless each is explicitly included by an approved method. PUE treatment, shared-host allocation, idle power allocation, and embodied emissions are TBD.

## Calculation paths

1. **Measured controlled machine:** use energy-counter delta where available; otherwise integrate timestamped power samples. Label incomplete sampling/coverage.
2. **Calculated emissions:** pair qualifying measured/calculated energy with a time- and region-matched carbon intensity.
3. **Estimated workload:** use only a reviewed estimation model; show input coverage, model version, confidence/uncertainty and non-applicable fields.
4. **Forecast scenario:** pair projected workload/scheduling assumptions with explicitly forecast intensity, separately from historical actuals.

No path may convert model name, cloud region, hardware TDP, or token count alone into a measurement. It can only support an estimate whose method has been validated for the stated boundary.

## Benchmarking and comparisons

Benchmark cohorts require matching or explicitly stratified model family/version, hardware, region, inference/training mode, token accounting convention, calculation boundary, formula version, and time window. The system should surface sample count, coverage, median/percentiles, evidence mix and excluded records. Rankings must be suppressed or qualified when records are not comparable.

## Recommendations

Recommendations are decision support, not autonomous execution. Each recommendation states the objective (for example lower estimated carbon), constraints, baseline, candidate, expected metric, evidence level, uncertainty and reason. Initial rule categories are model right-sizing, model/hardware/region comparison, scheduling opportunities, and token-efficiency signals. Cost, latency, quality, availability and data-residency constraints are inputs where supplied; otherwise their status is unknown.

## Validation checks

- Timestamps use UTC and duration must be non-negative.
- Units must be explicit before conversion.
- Token totals cannot be negative; absence is different from zero.
- Carbon intensity must be non-negative and temporally/geographically compatible.
- Energy/emission totals preserve the lineage of every included value.
- Re-running identical inputs with the same formula/source versions must yield the same result.
