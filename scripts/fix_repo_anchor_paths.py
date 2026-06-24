#!/usr/bin/env python3
"""Repository documentation anchor indexer for code generation.

Anchor rule:
- Load Markdown documentation from:
  - /docs/architecture/*
  - /docs/specs/*
  - /docs/api/*
  - /docs/data/*
  - /docs/integrations/*
  - /docs/qc/*
- Treat these directories as authoritative for code generation.
- Stop with a non-zero exit code if any required directory is missing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

REQUIRED_DOC_PATHS = [
    "docs/architecture",
    "docs/specs",
    "docs/api",
    "docs/data",
    "docs/integrations",
    "docs/qc",
]

AUTHORITATIVE_DOMAINS = {
    "docs/architecture": "system_architecture",
    "docs/specs": "service_definitions",
    "docs/api": "api_contracts",
    "docs/data": "data_models",
    "docs/integrations": "integration_specs",
    "docs/qc": "validation_constraints",
}


def validate_required_paths(repo_root: Path) -> List[str]:
    missing = [rel for rel in REQUIRED_DOC_PATHS if not (repo_root / rel).is_dir()]
    return missing


def detect_spec_files(repo_root: Path) -> List[Path]:
    """Detect all authoritative specification docs from required docs folders."""
    files: List[Path] = []
    for rel_dir in REQUIRED_DOC_PATHS:
        files.extend(sorted((repo_root / rel_dir).glob("*.md")))
    return sorted(files)


def classify(path: Path, repo_root: Path) -> str:
    rel_parent = str(path.parent.relative_to(repo_root))
    return AUTHORITATIVE_DOMAINS.get(rel_parent, "unknown")


def build_spec_index(repo_root: Path, spec_files: List[Path]) -> Dict[str, object]:
    """Build internal spec index after reading all authoritative docs."""
    index: Dict[str, object] = {
        "anchor_rule": "docs_subdirectories",
        "required_paths": REQUIRED_DOC_PATHS,
        "authoritative_domains": list(AUTHORITATIVE_DOMAINS.values()),
        "documents": [],
    }

    for path in spec_files:
        content = path.read_text(encoding="utf-8")
        index["documents"].append(
            {
                "file": str(path.relative_to(repo_root)),
                "domain": classify(path, repo_root),
                "bytes": len(content.encode("utf-8")),
                "chars": len(content),
            }
        )

    return index


def main() -> int:
    repo_root = Path.cwd()

    missing_paths = validate_required_paths(repo_root)
    if missing_paths:
        print(
            json.dumps(
                {
                    "error": "Missing required documentation path(s)",
                    "missing": missing_paths,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1

    spec_files = detect_spec_files(repo_root)
    spec_index = build_spec_index(repo_root, spec_files)

    (repo_root / "spec_index.json").write_text(
        json.dumps(spec_index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    output = {
        "spec_files_detected": [str(p.relative_to(repo_root)) for p in spec_files],
        "spec_index_created": "spec_index.json",
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
