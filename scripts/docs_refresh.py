#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = ["cyclopts==4.25.2"]
# ///
"""Refresh existing documents from the shared documentation library.

Run ``uv run --script scripts/docs_refresh.py --dry-run`` to preview updates.
Cyclopts is the only dependency; HTTPS and ZIP handling use the standard library.
"""

import io
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import cyclopts

ARCHIVE_URL = (
    "https://codeload.github.com/leynos/agent-helper-scripts/zip/refs/heads/main"
)
LIBRARY_PREFIX = "agent-helper-scripts-main/documentation-library/"
DEFAULT_DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"
app = cyclopts.App()


def load_reference_documents() -> dict[str, bytes]:
    """Download one snapshot of the upstream library without extracting files.

    For example, the result maps ``"scripting-standards.md"`` to its bytes.

    Returns
    -------
    dict[str, bytes]
        Library contents keyed by their relative paths.

    Raises
    ------
    ValueError
        If the archive contains no reference documents.
    """
    with urllib.request.urlopen(ARCHIVE_URL, timeout=60) as response:
        archive_bytes = response.read()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        documents = {
            entry.filename.removeprefix(LIBRARY_PREFIX): archive.read(entry)
            for entry in archive.infolist()
            if entry.filename.startswith(LIBRARY_PREFIX) and not entry.is_dir()
        }
    if not documents:
        message = "The upstream archive contains no documentation-library files"
        raise ValueError(message)
    return documents


def refresh_documents(
    docs_dir: Path, references: dict[str, bytes], *, is_dry_run: bool = False
) -> list[str]:
    """Replace differing local documents that have matching reference paths.

    For example, ``refresh_documents(docs, {"guide.md": b"new"})`` updates
    ``docs/guide.md`` only if that regular file already exists and differs.
    Symbolic links are skipped so updates stay within the documentation tree.

    Returns
    -------
    list[str]
        Changed paths relative to the documentation directory, in sorted order.
    """
    changed = []
    for path in sorted(docs_dir.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        relative_path = path.relative_to(docs_dir).as_posix()
        reference = references.get(relative_path)
        if reference is None or path.read_bytes() == reference:
            continue
        if not is_dry_run:
            path.write_bytes(reference)
        changed.append(relative_path)
    return changed


@app.default
def main(*, docs_dir: Path = DEFAULT_DOCS_DIR, dry_run: bool = False) -> None:
    """Update matching documents from leynos/agent-helper-scripts main.

    For example, ``--docs-dir /tmp/project/docs --dry-run`` previews updates
    for another checkout without writing files.

    Raises
    ------
    NotADirectoryError
        Detected for missing directories and reported as an exit status below.
    SystemExit
        With status 1 when downloading, reading, or writing documents fails.
    """
    try:
        if not docs_dir.is_dir():
            message = f"Documentation directory does not exist: {docs_dir}"
            raise NotADirectoryError(message)
        references = load_reference_documents()
        changed = refresh_documents(docs_dir, references, is_dry_run=dry_run)
    except (OSError, urllib.error.URLError, zipfile.BadZipFile, ValueError) as exc:
        print(f"Documentation refresh failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    verb = "Would update" if dry_run else "Updated"
    for relative_path in changed:
        print(f"{verb} {relative_path}")
    print(f"{len(changed)} document(s) {'would be updated' if dry_run else 'updated'}.")


if __name__ == "__main__":
    app()
