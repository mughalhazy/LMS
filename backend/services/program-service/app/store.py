from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from .models import Program


class ProgramStore(Protocol):
    def create(self, program: Program) -> Program: ...

    def update(self, program: Program) -> Program: ...

    def get(self, program_id: str) -> Program | None: ...

    def list_by_tenant(self, tenant_id: str) -> list[Program]: ...

    def code_exists(self, tenant_id: str, code: str) -> bool: ...


class InMemoryProgramStore:
    def __init__(self) -> None:
        self._programs: dict[str, Program] = {}

    def create(self, program: Program) -> Program:
        self._programs[program.program_id] = replace(program)
        return program

    def update(self, program: Program) -> Program:
        self._programs[program.program_id] = replace(program)
        return program

    def get(self, program_id: str) -> Program | None:
        program = self._programs.get(program_id)
        return replace(program) if program else None

    def list_by_tenant(self, tenant_id: str) -> list[Program]:
        return [replace(p) for p in self._programs.values() if p.tenant_id == tenant_id and not p.deleted]

    def code_exists(self, tenant_id: str, code: str) -> bool:
        return any(p.tenant_id == tenant_id and p.code == code and not p.deleted for p in self._programs.values())
