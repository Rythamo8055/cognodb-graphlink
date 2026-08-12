"""Domain registry - the three networks served by the same graph engine.

Each domain module exports ``META`` (the domain config described in
CONTRACT.md) and ``build_dataset()`` returning ``{"nodes", "edges", "meta"}``
in the shared dataset format. The registry is the single place that decides
which domains exist and in which order they appear in the UI.
"""
from functools import lru_cache

from . import education, healthcare, investors

DOMAINS = [investors, education, healthcare]


def list_domains():
    """Ordered META dicts for every domain (used by /api/domains)."""
    return [m.META for m in DOMAINS]


def get_domain(domain_id):
    """Return the domain module, raising KeyError for unknown ids."""
    for m in DOMAINS:
        if m.META["id"] == domain_id:
            return m
    raise KeyError(domain_id)


@lru_cache(maxsize=None)
def get_dataset(domain_id):
    """Cached build_dataset() result for a domain."""
    return get_domain(domain_id).build_dataset()
