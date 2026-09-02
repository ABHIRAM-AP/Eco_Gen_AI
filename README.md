# EcoGen-AI

EcoGen-AI is a proposed research-oriented framework for tracking and optimising the energy consumption and carbon emissions of generative-AI workloads. It is designed to combine controlled-machine measurements with transparent calculations and carefully labelled estimates—not to claim universal visibility into private data centres.

## Current status

Planning and architecture only. This repository intentionally contains no application implementation yet.

## Intended capabilities

- Ingest GenAI workload metadata: tokens, model, duration, region and available execution details.
- Collect CPU/GPU utilisation and power/energy only where hardware is controlled or integration access is granted.
- Calculate energy and electricity-related emissions with explicit boundaries and provenance.
- Compare compatible workload/model/hardware/region scenarios.
- Provide explainable recommendations for model sizing, hardware/region choices, scheduling and token efficiency.

## Documentation

- [Architecture](docs/architecture.md)
- [Data sources and evidence policy](docs/data-sources.md)
- [Calculation boundaries and methodology](docs/calculations.md)
- [Phased implementation plan](docs/implementation-plan.md)

## Technology direction

The proposed stack is Next.js/React/TypeScript/Tailwind/shadcn-ui/ECharts/MapLibre; FastAPI/Pydantic; PostgreSQL/TimescaleDB; optional Redis; Pandas/NumPy/scikit-learn/XGBoost; OR-Tools; OpenTelemetry/CodeCarbon/NVIDIA NVML where applicable; and Docker Compose for the first deployment.

Specific external datasets and APIs are not selected yet. They remain TBD until source coverage, licensing, methodology and reproducibility are reviewed.
