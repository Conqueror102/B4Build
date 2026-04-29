"""Tests for RDS CA bundle merge into asyncpg connect_args."""

from __future__ import annotations

import ssl

import certifi

from src.database_url import merge_postgres_ssl_with_rds_ca_bundle


def test_merge_keeps_ssl_true_when_bundle_missing() -> None:
    args = {"ssl": True}
    assert merge_postgres_ssl_with_rds_ca_bundle(args, "/no/such/rds-global-bundle.pem") == args


def test_merge_keeps_ssl_true_when_path_empty() -> None:
    args = {"ssl": True}
    assert merge_postgres_ssl_with_rds_ca_bundle(args, None) == args
    assert merge_postgres_ssl_with_rds_ca_bundle(args, "") == args


def test_merge_replaces_true_with_ssl_context_when_ca_file_readable() -> None:
    out = merge_postgres_ssl_with_rds_ca_bundle({"ssl": True}, certifi.where())
    assert isinstance(out["ssl"], ssl.SSLContext)


def test_merge_leaves_empty_connect_args() -> None:
    assert merge_postgres_ssl_with_rds_ca_bundle({}, certifi.where()) == {}
