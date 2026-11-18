"""Thin wrapper around the Waves (Models) API, one module per feature.

Each call goes through utils.http / utils.ws, so it is logged as evidence and
returns the raw server behavior (status, headers, frames) rather than hiding it
the way an SDK would.
"""
