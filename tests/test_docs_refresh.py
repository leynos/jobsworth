"""Verify document refresh boundaries against an in-memory upstream archive."""

import io
import tempfile
import urllib.error
import zipfile
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pytest_bdd import given as given_step
from pytest_bdd import scenario, then, when

from scripts import docs_refresh


@pytest.fixture
def upstream_archive() -> bytes:
    """Provide a reference snapshot with a matching guide and an absent guide.

    Returns
    -------
    bytes
        An upstream archive suitable for the HTTPS response double.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(docs_refresh.LIBRARY_PREFIX + "guide.md", b"Latest guide\n")
        archive.writestr(docs_refresh.LIBRARY_PREFIX + "new.md", b"New guide\n")
        archive.writestr("agent-helper-scripts-main/README.md", b"Not a reference\n")
    return buffer.getvalue()


@scenario("features/docs_refresh.feature", "Refresh only existing reference documents")
def test_refresh_cli() -> None:
    """Exercise the CLI, archive parser, and filesystem as one workflow."""


@given_step(
    "a documentation directory with a shared guide and a project guide",
    target_fixture="local_documents",
)
def local_documents(tmp_path: Path) -> Path:
    """Create local documentation with one upstream match.

    Returns
    -------
    Path
        The documentation directory used by the CLI scenario.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_bytes(b"Old guide\n")
    (docs_dir / "project.md").write_bytes(b"Project guide\n")
    return docs_dir


@when("the refresh command downloads the latest reference archive")
def run_refresh(
    local_documents: Path,
    upstream_archive: bytes,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Replace the HTTPS response while retaining the real command path."""
    with (
        mock.patch.object(
            docs_refresh.urllib.request,
            "urlopen",
            return_value=io.BytesIO(upstream_archive),
        ) as download,
        pytest.raises(SystemExit) as exit_info,
    ):
        docs_refresh.app(["--docs-dir", str(local_documents)])
    assert exit_info.value.code == 0, "A valid reference archive must refresh cleanly"
    download.assert_called_once_with(docs_refresh.ARCHIVE_URL, timeout=60)
    assert "Updated guide.md" in capsys.readouterr().out, "Report each updated document"


@then("only the shared guide is replaced and the update is reported")
def verify_refresh(local_documents: Path) -> None:
    """Keep project-specific content and absent reference files untouched."""
    why = "Matching shared guides must use upstream bytes"
    assert (local_documents / "guide.md").read_bytes() == b"Latest guide\n", why
    why = "Project-specific guides must retain local bytes"
    assert (local_documents / "project.md").read_bytes() == b"Project guide\n", why
    assert not (local_documents / "new.md").exists(), "Do not import absent documents"


def test_dry_run_preserves_documents(tmp_path: Path, upstream_archive: bytes) -> None:
    """Preview updates through the CLI without modifying local bytes."""
    guide = tmp_path / "guide.md"
    guide.write_bytes(b"Original\n")
    with (
        mock.patch.object(
            docs_refresh.urllib.request,
            "urlopen",
            return_value=io.BytesIO(upstream_archive),
        ),
        pytest.raises(SystemExit) as exit_info,
    ):
        docs_refresh.app(["--docs-dir", str(tmp_path), "--dry-run"])
    assert exit_info.value.code == 0, "Dry runs must succeed"
    assert guide.read_bytes() == b"Original\n", "Dry runs must preserve document bytes"


def test_nested_paths_and_symlinks(tmp_path: Path) -> None:
    """Match relative paths precisely and avoid writing through symbolic links."""
    docs_dir = tmp_path / "docs"
    nested = docs_dir / "nested"
    nested.mkdir(parents=True)
    (nested / "guide.md").write_bytes(b"Old nested\n")
    outside = tmp_path / "outside.md"
    outside.write_bytes(b"Outside\n")
    (docs_dir / "linked.md").symlink_to(outside)
    (docs_dir / "linked-dir").symlink_to(tmp_path, target_is_directory=True)
    references = {
        "nested/guide.md": b"New nested\n",
        "guide.md": b"Wrong path\n",
        "linked.md": b"Unsafe\n",
        "linked-dir/outside.md": b"Unsafe\n",
    }
    changed = docs_refresh.refresh_documents(docs_dir, references)
    assert changed == ["nested/guide.md"], "Only exact regular-file matches may change"
    why = "Nested guides must use their matching reference path"
    assert (nested / "guide.md").read_bytes() == b"New nested\n", why
    assert outside.read_bytes() == b"Outside\n", "Link targets must remain untouched"


@given(original=st.binary(), replacement=st.binary())
def test_refresh_converges(original: bytes, replacement: bytes) -> None:
    """Arbitrary document bytes converge after one refresh and remain stable."""
    # A fresh directory per example prevents state leaking across Hypothesis runs.
    with tempfile.TemporaryDirectory() as directory:
        docs_dir = Path(directory)
        guide = docs_dir / "guide.md"
        guide.write_bytes(original)
        references = {"guide.md": replacement}
        first = docs_refresh.refresh_documents(docs_dir, references)
        why = "Report a change exactly when bytes differ"
        assert first == ([] if original == replacement else ["guide.md"]), why
        assert guide.read_bytes() == replacement, "Refreshed bytes must match upstream"
        why = "A repeated refresh must leave the document unchanged"
        assert not docs_refresh.refresh_documents(docs_dir, references), why


@pytest.mark.parametrize(
    "failure",
    [
        urllib.error.URLError("Network unavailable"),
        zipfile.BadZipFile("Invalid archive"),
        ValueError("No reference documents"),
    ],
    ids=["network", "archive", "library"],
)
def test_download_failure_preserves_documents(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], failure: Exception
) -> None:
    """Download failures must produce actionable errors before any writes."""
    guide = tmp_path / "guide.md"
    guide.write_bytes(b"Original\n")
    with (
        mock.patch.object(
            docs_refresh, "load_reference_documents", side_effect=failure
        ),
        pytest.raises(SystemExit) as exit_info,
    ):
        docs_refresh.app(["--docs-dir", str(tmp_path)])
    assert exit_info.value.code == 1, "Refresh failures must exit unsuccessfully"
    why = "Failures must include an actionable diagnostic"
    assert "Documentation refresh failed" in capsys.readouterr().err, why
    assert guide.read_bytes() == b"Original\n", "Failed downloads must preserve files"


@pytest.mark.parametrize(
    ("payload", "expected_error", "diagnostic"),
    [
        (b"not a zip", zipfile.BadZipFile, "not a zip file"),
        (b"", zipfile.BadZipFile, "not a zip file"),
        (None, ValueError, "no documentation-library"),
    ],
    ids=["invalid", "empty", "missing-library"],
)
def test_unusable_archive_is_rejected(
    payload: bytes | None, expected_error: type[Exception], diagnostic: str
) -> None:
    """Invalid responses and unexpected library layouts must fail visibly."""
    if payload is None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("unexpected/README.md", "No library here")
        payload = buffer.getvalue()
    with (
        mock.patch.object(
            docs_refresh.urllib.request, "urlopen", return_value=io.BytesIO(payload)
        ),
        pytest.raises(expected_error, match=diagnostic),
    ):
        docs_refresh.load_reference_documents()


def test_missing_docs_directory(tmp_path: Path) -> None:
    """Reject a missing target before attempting a network request."""
    with (
        mock.patch.object(docs_refresh, "load_reference_documents") as download,
        pytest.raises(SystemExit) as exit_info,
    ):
        docs_refresh.app(["--docs-dir", str(tmp_path / "missing")])
    assert exit_info.value.code == 1, "Missing directories must fail"
    download.assert_not_called()
