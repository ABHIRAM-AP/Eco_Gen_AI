# Data Sources and Evidence Policy

## Source categories

EcoGen-AI will integrate a source only after its identity, licence/terms, geographic and temporal coverage, refresh behaviour, units, access method, and citation requirements are documented. Specific datasets and APIs are **TBD**; this project must not claim a source exists merely because a category is desired.

| Category | Intended use | Permitted evidence | Key limitation |
| --- | --- | --- | --- |
| Workload telemetry | Request duration, model metadata, token counts, execution context. | Application instrumentation and OpenTelemetry attributes. | Providers may not expose all fields. |
| Controlled-host telemetry | CPU/GPU utilisation, power, energy, hardware identity. | CodeCarbon, NVIDIA NVML where applicable, OS/hardware interfaces. | Only for machines controlled or explicitly accessible to the operator. |
| Cloud-region catalogues | Region names, locations and public infrastructure attributes. | Public cloud-provider documentation/catalogues. | Does not reveal private hardware configuration or per-request energy. |
| Hardware references | Rated characteristics, architecture/specification and benchmark context. | Public manufacturer documentation and reputable published benchmarks, subject to review. | Ratings are not equivalent to observed workload power. |
| Carbon intensity | Convert energy to emissions using time/region-appropriate intensity. | Public/API source with documented scope and timestamp. | Coverage, method, latency and licensing vary; gaps remain unknown. |
| Forecast carbon intensity | Carbon-aware scheduling scenarios. | Explicit forecast-capable source or project model, documented separately. | Never present forecast as an observation. |

## Required source metadata

Each imported reference value/snapshot must record: source name, publisher, canonical URL or API endpoint identifier, licence/terms status, retrieval timestamp, effective time range, geography/region mapping, unit, method/version when supplied, raw payload or retained reference where lawful, parser version, and quality/coverage notes.

## Source lifecycle

1. Propose and review the source against the required metadata.
2. Implement an adapter with schema validation and unit conversion tests.
3. Store an immutable, versioned snapshot before it is used in calculations.
4. Map provider region labels to an internal canonical region record; unmapped labels remain unresolved.
5. Monitor refresh/failure status and retain the last known value with its validity, never relabelling it as current.
6. Cite the exact snapshot/source version in result lineage.

## Data-quality rules

- Missing token count, region, duration, power, energy, or carbon intensity is represented as missing, not zero.
- Regional carbon intensity must include time, geography and unit. Do not apply a national average to a cloud region without an explicit documented mapping/assumption.
- Hardware TDP, nameplate power and benchmark values are reference inputs for estimates, not measurements.
- Cloud provider documentation can establish a region but cannot establish hidden fleet hardware, utilisation, PUE, or request-level energy unless the provider publishes it for that scope.
- A user-supplied value must retain `user_declared` origin and is not automatically authoritative.
- Default emission-factor treatment beyond electricity carbon intensity (for example embodied emissions) is TBD and excluded until a defensible source/method is approved.

## Initial source decisions

No external dataset or API is selected in this plan. Initial development should use clearly labelled synthetic fixtures and controlled-host test telemetry only. Selecting production sources is a dedicated discovery and governance deliverable.
