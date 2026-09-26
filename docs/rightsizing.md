# Resource Utilization & Rightsizing Log

Use this document to record telemetry observations, RAM usage benchmarks, and CPU load metrics from Grafana over time.

---

## Baseline Target Limits

- **Platform VM (`8GB RAM`)**: Target steady-state memory utilization `< 6.5 GB` (leave ~1.5 GB overhead for peak Docker build spikes).
- **App VM (`4GB RAM`)**: Target steady-state memory utilization `< 3.2 GB` (leave ~800 MB overhead for Playwright Firefox spikes in `bus-scraper`).

---

## Observation Log

| Date | Platform VM RAM | App VM RAM | Peak CPU Load | Notes / Recommendations |
| :--- | :--- | :--- | :--- | :--- |
| 2026-09-26 | - | - | - | Initial scaffold deployment. |
