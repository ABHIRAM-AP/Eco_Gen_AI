# Implementation Plan

## Database entities

PostgreSQL stores transactional/reference metadata; TimescaleDB hypertables store sampled measurements and high-volume event series. Exact columns, keys, retention and partitioning are TBD during schema design.

| Entity | Purpose |
| --- | --- |
| Workspace, User, Role | Tenant and access boundary (authentication design TBD). |
| Workload | Named monitored workload/configuration and declared execution context. |
| WorkloadRequest | One GenAI request/run: timestamps, model/provider metadata, known input/output tokens, duration and trace correlation. |
| ExecutionEnvironment | Controlled machine, user-declared environment or provider/region context; capabilities and ownership scope. |
| HardwareProfile | Versioned hardware identity/specification/reference metadata, distinct from a private-cloud assertion. |
| TelemetryMeasurement | Timestamped CPU/GPU/utilisation/power/energy measurement, source and quality fields (TimescaleDB). |
| Region | Canonical region/geographic mapping and provider label mappings. |
| CarbonIntensityObservation | Time-bounded regional observed intensity with source snapshot/version (TimescaleDB where series volume warrants it). |
| CarbonIntensityForecast | Separate future intensity series and forecast metadata. |
| ReferenceSource and SourceSnapshot | Source governance, raw/parsed snapshot lineage and validity. |
| CalculationRun and MetricResult | Formula/model version, inputs, boundary, provenance, quality, uncertainty and output values. |
| BenchmarkDefinition and BenchmarkResult | Cohort criteria, aggregation window and comparability/evidence summary. |
| Recommendation | Baseline/candidate, constraints, rationale, expected impact, evidence and status. |
| ImportJob / BackgroundJob | Asynchronous progress, error and retry lineage if workers are introduced. |

## API boundaries (proposed `/api/v1`)

| Area | Endpoints / responsibility |
| --- | --- |
| Ingestion | `POST /ingestion/workload-events`, `POST /ingestion/measurements`; idempotent accepted/rejected event reporting. |
| Workloads | Create/read/update workload metadata; list requests with privacy-safe fields. |
| Reference data | Read regions, hardware profiles, source provenance and coverage; administrative import/refresh endpoints are TBD. |
| Analytics | Submit calculation, retrieve calculation/job status and metrics with lineage. |
| Comparison | Define/query benchmark cohorts and model/hardware/region comparisons. |
| Recommendations | List, explain, acknowledge/dismiss recommendations; no automatic execution endpoint. |
| Platform | Health/readiness, authentication/session endpoints (TBD), API schema/version metadata. |

The API accepts and returns typed Pydantic schemas. It is responsible for request validation and authorization; it delegates formulas to the analytics package. Pagination, filtering, rate limits, error envelope and API authentication scheme are TBD before implementation.

## Development phases

### Phase 0 — Research contract and foundations

Confirm the supplied abstract, research questions, non-functional requirements, privacy policy, target deployment environment, and evaluation criteria. Select and document permitted data sources. Define canonical units, provenance taxonomy, calculation boundaries, uncertainty representation and acceptance metrics.

### Phase 1 — Project scaffold and data contract

Create Docker Compose, FastAPI and Next.js skeletons; database migrations; typed domain schemas; OpenAPI contract; CI formatting/linting/test baseline. Seed only synthetic, clearly labelled fixtures. No claim of real-world coverage.

### Phase 2 — Controlled workload ingestion and transparent analytics MVP

Implement workload event ingestion, controlled-host telemetry adapter interface, request/measurement storage, first calculation path for complete measured energy, carbon-intensity join only for an approved source, and a dashboard that exposes lineage/missing data.

### Phase 3 — Estimation, comparisons and monitoring integrations

Add an approved/calibrated estimation model, CodeCarbon/NVML integrations where applicable, workload benchmarks and model/hardware/region comparison screens. Evaluate estimates against controlled measurements and publish error/coverage results.

### Phase 4 — Decision support and optimisation research

Implement transparent rule recommendations, then constrained optimisation (OR-Tools) after objective functions and constraints are validated. Add carbon-aware scheduling only if a selected forecast source supports it.

### Phase 5 — Hardening and project evaluation

Security/privacy review, retention controls, observability, load/reliability tests, reproducibility package, user evaluation, methodology limitations and final research report.

## Testing strategy

| Level | Focus |
| --- | --- |
| Unit | Unit conversion, formula edge cases, provenance propagation, validation, region/time matching, recommendation rules. |
| Property/contract | Non-negative and dimensional invariants; Pydantic/OpenAPI API contract compatibility. |
| Integration | FastAPI-to-Postgres/TimescaleDB migrations, idempotent ingestion, source snapshot persistence and calculation lineage. |
| Fixture-based | Deterministic synthetic traces including missing/partial/out-of-order telemetry and known expected outcomes. |
| Adapter | Source/monitoring payload parsing against captured, permitted fixtures; no live source required in routine CI. |
| End-to-end | Critical dashboard flows: ingest → calculate → inspect provenance → compare/recommend. |
| Scientific validation | Compare approved estimates against controlled-machine measurements; report error, uncertainty, scope and failures. |
| Security/performance | Authz isolation once selected, secret/prompt-data leakage checks, retention tests, ingestion throughput and query latency. |

## Delivery gates

Do not proceed from a phase without documented source provenance, reproducible test fixtures, migration rollback/upgrade validation, and UI/API evidence labels appropriate to the features delivered. Estimated or forecast results require explicit validation criteria before being shown as decision support.
