from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/operations-os/service.py"

spec = importlib.util.spec_from_file_location("operations_os_module_for_qc", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load operations-os module")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


if __name__ == "__main__":
    service = module.OperationsOSService()
    if service.has_business_logic_duplication():
        raise SystemExit("QC failed: business logic duplication detected")
    print("QC passed: operations-os aggregates owner services without logic duplication")
