from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/system-of-record/service.py"
spec = importlib.util.spec_from_file_location("system_of_record_qc_module", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load system-of-record module")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

SystemOfRecordService = module.SystemOfRecordService


def run_qc() -> dict[str, bool]:
    service = SystemOfRecordService()
    qc_report = service.run_qc_autofix()
    return {
        "single_source_of_truth": service.is_single_source_of_truth(),
        "duplicate_data_ownership": not service.has_duplicate_data_ownership(),
        **qc_report,
    }
