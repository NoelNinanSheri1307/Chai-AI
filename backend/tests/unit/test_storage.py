"""Tests for the local storage adapter."""

from __future__ import annotations

import pytest

from app.clients.storage import (
    LocalStorageAdapter,
    StorageClient,
    StorageError,
    StorageObjectNotFoundError,
)


def test_store_fetch_round_trip(storage: LocalStorageAdapter) -> None:
    storage.store("dev/orig/abc.png", b"image-bytes", content_type="image/png")
    assert storage.fetch("dev/orig/abc.png") == b"image-bytes"


def test_store_overwrites_existing_object(storage: LocalStorageAdapter) -> None:
    storage.store("a.txt", b"first")
    storage.store("a.txt", b"second")
    assert storage.fetch("a.txt") == b"second"


def test_exists_reflects_stored_objects(storage: LocalStorageAdapter) -> None:
    assert storage.exists("a.txt") is False
    storage.store("a.txt", b"x")
    assert storage.exists("a.txt") is True


def test_delete_returns_whether_object_existed(storage: LocalStorageAdapter) -> None:
    storage.store("a.txt", b"x")
    assert storage.delete("a.txt") is True
    assert storage.delete("a.txt") is False


def test_fetch_missing_object_raises(storage: LocalStorageAdapter) -> None:
    with pytest.raises(StorageObjectNotFoundError):
        storage.fetch("missing.txt")


def test_nested_keys_create_directories(storage: LocalStorageAdapter) -> None:
    storage.store("env/orig/deep/path/img.png", b"bytes")
    assert (storage.root / "env" / "orig" / "deep" / "path" / "img.png").is_file()


def test_storage_root_is_created(storage_root) -> None:
    LocalStorageAdapter(storage_root)
    assert storage_root.is_dir()


def test_empty_and_null_key_rejected(storage: LocalStorageAdapter) -> None:
    with pytest.raises(StorageError):
        storage.store("", b"x")
    with pytest.raises(StorageError):
        storage.store("\x00bad", b"x")


def test_path_traversal_rejected(storage: LocalStorageAdapter) -> None:
    with pytest.raises(StorageError):
        storage.store("../escape.png", b"x")
    with pytest.raises(StorageError):
        storage.store("a/../../escape.png", b"x")
    with pytest.raises(StorageError):
        storage.store("/abs/path.png", b"x")
    with pytest.raises(StorageError):
        storage.store("a\\..\\escape.png", b"x")


def test_delete_and_fetch_guard_against_traversal(storage: LocalStorageAdapter) -> None:
    with pytest.raises(StorageError):
        storage.fetch("../../etc/passwd")
    with pytest.raises(StorageError):
        storage.delete("..\\..\\etc\\passwd")


def test_concrete_implements_storage_client_interface(
    storage: LocalStorageAdapter,
) -> None:
    assert isinstance(storage, StorageClient)
    with pytest.raises(NotImplementedError):
        storage.signed_url("a.txt", ttl_seconds=60)
