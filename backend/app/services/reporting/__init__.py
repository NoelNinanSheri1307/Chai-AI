"""Report construction.

Typed, deterministic forensic report models and their builders. The report
layer only consumes already-produced analysis results — it never re-runs
detectors, fusion or heatmap generation — so the same analysis always yields
the same report.
"""
