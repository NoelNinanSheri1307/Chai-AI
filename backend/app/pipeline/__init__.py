"""Forensic pipeline.

Pure computation on an image file: signal extraction, fusion, verdict,
evidence, heatmap and optional LLM explanation. The pipeline is isolated from
HTTP and the database so it can be unit-tested and swapped independently. It
is implemented by the AI pipeline milestone (Milestone 7).
"""
