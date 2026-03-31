#!/usr/bin/env python3
"""Lightweight validator for prerequisite rule module JSON definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent
RULE_FILES = [
    "course-prerequisite.rules.json",
    "learning-path-prerequisites.rules.json",
    "completion-eligibility.rules.json",
]

ALLOWED_RULE_TYPES = {
    "course_prerequisite",
    "learning_path_dependency",
    "completion_based_eligibility",
}

ALLOWED_OPERATORS = {
    "equals",
    "greater_than_or_equal",
    "less_than_or_equal",
}


class ValidationError(Exception):
    """Domain-specific exception."""


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_envelope(doc: Dict, filename: str) -> None:
    required = ["rule_set_id", "service", "rule_type", "version", "rules"]
    missing = [field for field in required if field not in doc]
    if missing:
        raise ValidationError(f"{filename}: missing required fields {missing}")

    if doc["service"] != "prerequisite_engine_service":
        raise ValidationError(f"{filename}: service must be prerequisite_engine_service")

    if doc["rule_type"] not in ALLOWED_RULE_TYPES:
        raise ValidationError(f"{filename}: unknown rule_type {doc['rule_type']}")

    if not isinstance(doc["rules"], list) or not doc["rules"]:
        raise ValidationError(f"{filename}: rules must be a non-empty array")


def validate_unique_rule_ids(doc: Dict, filename: str) -> None:
    rule_ids = [rule.get("rule_id") for rule in doc["rules"]]
    if any(not rid for rid in rule_ids):
        raise ValidationError(f"{filename}: every rule must define rule_id")
    if len(set(rule_ids)) != len(rule_ids):
        raise ValidationError(f"{filename}: duplicate rule_id values detected")


def validate_course_prerequisites(doc: Dict, filename: str) -> None:
    for rule in doc["rules"]:
        groups = rule.get("requirement_groups", [])
        if not groups:
            raise ValidationError(f"{filename}:{rule['rule_id']}: requirement_groups required")
        for group in groups:
            if group.get("logic") not in {"all", "any"}:
                raise ValidationError(f"{filename}:{rule['rule_id']}: invalid group logic")
            if not group.get("courses"):
                raise ValidationError(f"{filename}:{rule['rule_id']}: group requires courses")


def has_cycle(nodes: List[str], edges: List[Dict[str, str]]) -> bool:
    adjacency: Dict[str, List[str]] = {node: [] for node in nodes}
    indegree: Dict[str, int] = {node: 0 for node in nodes}

    for edge in edges:
        src = edge["from"]
        dst = edge["to"]
        adjacency.setdefault(src, []).append(dst)
        indegree.setdefault(dst, 0)
        indegree[dst] += 1

    queue = [node for node, degree in indegree.items() if degree == 0]
    visited = 0

    while queue:
        current = queue.pop()
        visited += 1
        for nxt in adjacency.get(current, []):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    return visited != len(indegree)


def validate_learning_path_dependencies(doc: Dict, filename: str) -> None:
    for rule in doc["rules"]:
        nodes = rule.get("nodes", [])
        node_ids = [node.get("node_id") for node in nodes]
        if not nodes or any(not n for n in node_ids):
            raise ValidationError(f"{filename}:{rule['rule_id']}: nodes must include node_id")

        edges = rule.get("edges", [])
        for edge in edges:
            if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
                raise ValidationError(f"{filename}:{rule['rule_id']}: edge references unknown node")

        if has_cycle(node_ids, edges):
            raise ValidationError(f"{filename}:{rule['rule_id']}: dependency graph contains a cycle")


def validate_completion_eligibility(doc: Dict, filename: str) -> None:
    for rule in doc["rules"]:
        logic = rule.get("eligibility_logic")
        if logic not in {"all", "any"}:
            raise ValidationError(f"{filename}:{rule['rule_id']}: invalid eligibility_logic")

        conditions = rule.get("conditions", [])
        if not conditions:
            raise ValidationError(f"{filename}:{rule['rule_id']}: conditions required")

        for condition in conditions:
            operator = condition.get("operator")
            if operator not in ALLOWED_OPERATORS:
                raise ValidationError(
                    f"{filename}:{rule['rule_id']}: invalid operator {operator}"
                )


def validate_file(path: Path) -> None:
    doc = load_json(path)
    filename = path.name
    validate_envelope(doc, filename)
    validate_unique_rule_ids(doc, filename)

    rule_type = doc["rule_type"]
    if rule_type == "course_prerequisite":
        validate_course_prerequisites(doc, filename)
    elif rule_type == "learning_path_dependency":
        validate_learning_path_dependencies(doc, filename)
    elif rule_type == "completion_based_eligibility":
        validate_completion_eligibility(doc, filename)


def main() -> None:
    for filename in RULE_FILES:
        validate_file(ROOT / filename)
    print(f"Validated {len(RULE_FILES)} rule files successfully.")


if __name__ == "__main__":
    main()
