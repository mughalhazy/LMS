#!/usr/bin/env python3
"""Repository-root spec anchor indexer for code generation.

New anchor rule:
- Discover all `*.md` files in repository root (no `/docs` or `/specs` assumption)
- Read every discovered spec file
- Build an internal spec index
- Treat these root Markdown files as authoritative for code generation
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

AUTHORITATIVE_DOMAINS = [
    "architecture",
    "service_definitions",
    "api_contracts",
    "data_models",
    "integration_specs",
    "qc_reports",
]


CATEGORY_KEYWORDS = {
    "architecture": ["architecture", "design", "boundaries", "strategy"],
    "service_definitions": ["service", "domain", "map", "ownership"],
    "api_contracts": ["api", "rest", "gateway", "webhook", "lti", "sso", "scorm"],
    "data_models": ["schema", "model", "storage", "data"],
    "integration_specs": ["integration", "event", "sync", "pipeline", "bus"],
    "qc_reports": ["qc", "validation", "check", "report"],
}


def detect_spec_files(repo_root: Path) -> List[Path]:
    """Detect all authoritative specification docs from repository root."""
    return sorted(p for p in repo_root.glob("*.md") if p.is_file())


def classify(filename: str) -> List[str]:
    name = filename.lower()
    matched = [
        category
        for category, keywords in CATEGORY_KEYWORDS.items()
        if any(keyword in name for keyword in keywords)
    ]
    return matched or ["architecture"]


def build_spec_index(repo_root: Path, spec_files: List[Path]) -> Dict[str, object]:
    """Build internal spec index after reading all root spec docs."""
    index: Dict[str, object] = {
        "anchor_rule": "root_markdown_only",
        "authoritative_domains": AUTHORITATIVE_DOMAINS,
        "documents": [],
    }

    for path in spec_files:
        content = path.read_text(encoding="utf-8")
        index["documents"].append(
            {
                "file": path.name,
                "categories": classify(path.name),
                "bytes": len(content.encode("utf-8")),
                "chars": len(content),
            }
        )

    return index


def main() -> int:
    repo_root = Path.cwd()
    spec_files = detect_spec_files(repo_root)
    spec_index = build_spec_index(repo_root, spec_files)

    (repo_root / "spec_index.json").write_text(
        json.dumps(spec_index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    output = {
        "spec_files_detected": [p.name for p in spec_files],
        "spec_index_created": "spec_index.json",
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
