"""Data-access (repository) layer.

Repositories are the only modules with access to the database and object
storage, and they enforce per-identity scoping. None are implemented within
the foundation milestone; the modules below are extension points filled by the
database milestone (Milestone 3) and beyond.
"""
