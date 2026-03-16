from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class ProgramStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    RETIRED = "retired"


class ProgramVisibility(str, Enum):
    PRIVATE = "private"
    INSTITUTION = "institution"
    PUBLIC = "public"


class LinkStatus(str, Enum):
    LINKED = "linked"
    SUSPENDED = "suspended"
    UNLINKED = "unlinked"


class MappingStatus(str, Enum):
    MAPPED = "mapped"
    UNMAPPED = "unmapped"


ALLOWED_TRANSITIONS: dict[ProgramStatus, set[ProgramStatus]] = {
    ProgramStatus.DRAFT: {ProgramStatus.ACTIVE},
    ProgramStatus.ACTIVE: {ProgramStatus.ARCHIVED},
    ProgramStatus.ARCHIVED: {ProgramStatus.RETIRED},
    ProgramStatus.RETIRED: set(),
}


@dataclass
class ProgramInstitutionLink:
    program_id: str
    institution_id: str
    link_status: LinkStatus
    linked_at: datetime | None = None
    unlinked_at: datetime | None = None
    link_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgramCourseMap:
    program_id: str
    course_id: str
    sequence_order: int
    is_required: bool
    minimum_completion_pct: int | None = None
    availability_rule: dict[str, Any] | None = None
    mapping_status: MappingStatus = MappingStatus.MAPPED
    mapped_at: datetime | None = None
    unmapped_at: datetime | None = None


@dataclass
class ProgramStatusHistory:
    program_id: str
    from_status: ProgramStatus
    to_status: ProgramStatus
    changed_by: str
    change_reason: str
    changed_at: datetime


@dataclass
class Program:
    program_id: str
    tenant_id: str
    institution_id: str
    code: str
    title: str
    description: str | None
    status: ProgramStatus
    version: int
    visibility: ProgramVisibility
    start_date: date | None
    end_date: date | None
    metadata: dict[str, Any]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
    mapping_version: int = 0
    deleted: bool = False
    institution_link: ProgramInstitutionLink | None = None
    course_mappings: list[ProgramCourseMap] = field(default_factory=list)
    status_history: list[ProgramStatusHistory] = field(default_factory=list)
