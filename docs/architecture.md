# EcoGen-AI Architecture

## Purpose and scope

EcoGen-AI is a research-oriented web application for estimating and analysing the energy use and carbon emissions of generative-AI workloads, then presenting evidence-aware optimisation recommendations. It is not a universal monitor of private data centres. It combines measurements from machines under the operator's control with declared workload metadata and public cloud, hardware, and carbon-intensity sources when those sources are available and licensed for use.

Every result must retain a provenance class:

| Class | Meaning |
| --- | --- |
| Measured | Directly observed by an instrument or monitoring integration. |
| Calculated | Deterministically derived from measured or authoritative input values. |
| Estimated | Model-based value produced where direct measurement is unavailable. |
| Forecast | Forward-looking value based on an explicitly identified forecast source/model. |
| Unknown | Value is absent; the system must not silently substitute a fabricated value. |

## Logical architecture

```text
Workload SDK / OTEL -> Ingestion API -> validation & normalization -> PostgreSQL/TimescaleDB
Controlled-host monitors -> Ingestion API ------------------------^              |
Public source adapters -> source snapshots / reference catalogues ----------------+
                                                                              Analytical engine
                                                                                     |
                                                          calculations, benchmarks, recommendations
                                                                                     |
Next.js web client <---------------- REST API (FastAPI) <-------------------------+
```

The first deployment is a Docker Compose stack: Next.js frontend, FastAPI backend, PostgreSQL with TimescaleDB, and optional Redis only after a documented asynchronous-job need arises. Source collection and longer calculations run as background jobs; user-facing APIs read persisted results and can expose job status.

## Modules and ownership

| Module | Responsibility | Does not do |
| --- | --- | --- |
| Web application | Dashboard, workload submission/import, comparison, transparent result/provenance display. | Recalculate results independently. |
| API service | Authentication/authorisation (TBD), validation, query endpoints, job orchestration. | Invent missing telemetry or reference data. |
| Ingestion service | Accept OpenTelemetry-compatible workload events and controlled-host monitoring payloads; normalize units and timestamps. | Claim third-party private-cloud hardware measurements. |
| Reference-data service | Version public cloud-region, hardware, and carbon-intensity inputs with source metadata and validity periods. | Treat unpublished provider internals as facts. |
| Analytics engine | Produce energy/emissions metrics, confidence/provenance and comparability warnings. | Conflate measured and estimated values. |
| Optimisation engine | Rank feasible alternatives using declared constraints and evidence. | Automatically move workloads or make unsupported cost/performance claims. |
| Job worker (conditional) | Fetch permitted source data, process imports, calculate series and forecasts. | Become required before workload justifies it. |

## Deployment and boundaries

- The frontend communicates only with the versioned FastAPI REST boundary (`/api/v1`).
- The backend is the only component that accesses the database and reference-source credentials.
- Monitoring agents/SDKs send authenticated telemetry to ingestion endpoints; their deployment is limited to machines the project controls or where explicit integration permission exists.
- Raw or sensitive prompt content is out of scope by default. Store token counts and workload metadata, not prompt/completion text, unless a later privacy policy and user consent explicitly authorize it.
- API and worker share domain schemas/calculation packages; calculation logic is never duplicated in the client.

## Data flow

1. A workload integration supplies request identifiers, model/provider information, token counts where available, duration, declared region and execution context.
2. A controlled-host integration may add CPU/GPU utilisation, power/energy readings, hardware identity and sampling intervals.
3. The ingestion service validates, records original units/source/provenance, normalizes usable fields, and flags missing or inconsistent fields.
4. Reference adapters store versioned source snapshots and their validity windows. A value cannot be used until its source, timestamp and geographic scope are known.
5. The analytics engine selects an auditable calculation path: measured energy when complete enough; otherwise an explicitly labelled estimate. It joins the applicable carbon-intensity observation/forecast only when region and time resolution match.
6. Results, assumptions, warnings, formula version and input lineage are persisted. Benchmarking compares only compatible scopes and labels non-comparable records.
7. The API returns both displayed metrics and their evidence/provenance so the UI can explain uncertainty and missing data.

## Security, privacy, and research integrity

- Tenant/workspace isolation, roles, retention policy, authentication approach, and secrets management are TBD before multi-user deployment.
- Store source URLs/licences, retrieval time, parser/version and checksums where practical to make research results reproducible.
- Minimise personally identifiable and prompt data. Redact secrets from telemetry and logs.
- Preserve raw measurements immutably where feasible; derived records must be recalculable by formula/version.
- Display uncertainty, coverage gaps and assumptions alongside aggregate comparisons.

## Initial repository structure

```text
Eco_Gen_AI/
├── docs/                         # architecture, sources, methods and delivery plan
├── frontend/                     # Next.js/React/TypeScript application (phase 2)
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI routers and dependency boundaries
│   │   ├── domain/               # entities, schemas, value objects
│   │   ├── ingestion/            # OTEL and monitoring normalization
│   │   ├── analytics/            # calculation orchestration
│   │   ├── optimization/         # recommendation constraints/ranking
│   │   ├── reference_data/       # source adapters and versioning
│   │   └── persistence/          # repositories and migrations
│   └── tests/
├── monitoring/                   # controlled-host collector/integration examples (phase 3)
├── infra/                        # Docker Compose, database and deployment configuration
├── scripts/                      # repeatable data/admin tooling
├── shared/                       # optional generated API client/contracts (TBD)
└── README.md
```

This is a proposed structure only; no application directories are created in this planning phase.
