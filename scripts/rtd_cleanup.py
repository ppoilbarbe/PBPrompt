#!/usr/bin/env python3
"""Clean up old Read the Docs versions according to the project retention policy.

Retention policy
----------------
Given the current latest semver tag X.Y.Z:

Current major + current minor (X.Y.*), older patches
    Keep the 3 most recent patches before Z.

Current major (X.*), older minors (< Y)
    For each of the 3 most recent minor versions before Y,
    keep only the latest patch.

Older major versions (< X)
    For each of the 3 most recent major versions before X,
    keep only the latest release overall.

Everything outside these limits is deactivated (not deleted).
The pseudo-versions ``latest`` and ``stable`` are never touched.

Usage
-----
    python scripts/rtd_cleanup.py --token TOKEN [--project SLUG] [--dry-run]

The token must have write access to the RTD project (API v3).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import urllib.error
import urllib.request
from typing import NamedTuple

log = logging.getLogger(__name__)

# Pseudo-versions managed by RTD — never deactivate these.
ALWAYS_KEEP: frozenset[str] = frozenset({"latest", "stable"})

RTD_API = "https://readthedocs.org/api/v3"


# ---------------------------------------------------------------------------
# Version model
# ---------------------------------------------------------------------------


class SemVer(NamedTuple):
    """Parsed semver triplet with its original RTD slug."""

    major: int
    minor: int
    patch: int
    slug: str

    def __str__(self) -> str:
        return self.slug


def parse_semver(slug: str) -> SemVer | None:
    """Return a SemVer for *slug* if it matches vX.Y.Z, else None."""
    import re

    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", slug)
    if not m:
        return None
    return SemVer(int(m.group(1)), int(m.group(2)), int(m.group(3)), slug)


# ---------------------------------------------------------------------------
# RTD API helpers
# ---------------------------------------------------------------------------


def _rtd_request(
    method: str,
    url: str,
    token: str,
    payload: dict | None = None,
) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {method} {url}: {body_text}") from exc


def get_active_tag_versions(project: str, token: str) -> list[dict]:
    """Return all active tag versions for *project* (paginated)."""
    results: list[dict] = []
    url = f"{RTD_API}/projects/{project}/versions/?active=true&type=tag&limit=100"
    while url:
        data = _rtd_request("GET", url, token)
        results.extend(data.get("results", []))
        url = data.get("next")
    return results


def deactivate_version(project: str, slug: str, token: str, *, dry_run: bool) -> None:
    """Deactivate a single version via the RTD API."""
    url = f"{RTD_API}/projects/{project}/versions/{slug}/"
    if dry_run:
        log.info("[dry-run] would deactivate %s", slug)
    else:
        _rtd_request("PATCH", url, token, {"active": False})
        log.info("Deactivated %s", slug)


# ---------------------------------------------------------------------------
# Retention policy
# ---------------------------------------------------------------------------


def compute_slugs_to_keep(versions: list[SemVer]) -> set[str]:
    """Return the set of slugs that should remain active.

    Applies the project retention policy (see module docstring).
    """
    if not versions:
        return set()

    # Descending order: largest version first.
    ordered = sorted(versions, reverse=True)
    cur = ordered[0]
    cur_major, cur_minor, cur_patch = cur.major, cur.minor, cur.patch

    keep: set[str] = {cur.slug}

    # --- Current major.minor — keep the 3 most recent older patches ---
    same_minor = [
        v
        for v in ordered
        if v.major == cur_major and v.minor == cur_minor and v.patch < cur_patch
    ]
    for v in same_minor[:3]:
        keep.add(v.slug)

    # --- Current major, older minors — keep latest patch of 3 most recent ---
    seen_minors: list[int] = []
    for v in ordered:
        if v.major == cur_major and v.minor < cur_minor:
            if v.minor not in seen_minors:
                seen_minors.append(v.minor)
                keep.add(v.slug)  # first encountered = latest patch for this minor
            if len(seen_minors) == 3:
                break

    # --- Older majors — keep latest release of 3 most recent major versions ---
    seen_majors: list[int] = []
    for v in ordered:
        if v.major < cur_major:
            if v.major not in seen_majors:
                seen_majors.append(v.major)
                keep.add(v.slug)  # first encountered = latest release for this major
            if len(seen_majors) == 3:
                break

    return keep


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project",
        default="pbprompt",
        help="Read the Docs project slug (default: pbprompt)",
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Read the Docs API v3 token with write access",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without applying them",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    log.info("Fetching active tag versions for project '%s'…", args.project)
    raw = get_active_tag_versions(args.project, args.token)

    # Parse semver tags; skip pseudo-versions and non-semver entries.
    tag_versions: list[SemVer] = []
    for entry in raw:
        slug = entry.get("slug", "")
        if slug in ALWAYS_KEEP:
            continue
        parsed = parse_semver(slug)
        if parsed:
            tag_versions.append(parsed)
        else:
            log.debug("Skipping non-semver version: %s", slug)

    if not tag_versions:
        log.info("No semver tag versions found — nothing to do.")
        return 0

    keep = compute_slugs_to_keep(tag_versions)
    to_deactivate = [v for v in tag_versions if v.slug not in keep]

    log.info(
        "Versions to keep (%d): %s",
        len(keep),
        ", ".join(sorted(keep)),
    )
    if not to_deactivate:
        log.info("No versions to deactivate.")
        return 0

    log.info(
        "Versions to deactivate (%d): %s",
        len(to_deactivate),
        ", ".join(v.slug for v in to_deactivate),
    )

    errors = 0
    for v in to_deactivate:
        try:
            deactivate_version(args.project, v.slug, args.token, dry_run=args.dry_run)
        except RuntimeError as exc:
            log.error("Failed to deactivate %s: %s", v.slug, exc)
            errors += 1

    if errors:
        log.error("%d error(s) occurred.", errors)
        return 1

    log.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
