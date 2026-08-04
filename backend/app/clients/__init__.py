"""External client adapters.

Clients talk to backing systems and optional external providers behind narrow
interfaces so the rest of the application can be tested with fakes. They are
implemented by their milestones: storage (Milestone 4), sightengine and
openrouter (optional providers), cache (hardening).
"""
