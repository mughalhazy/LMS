"""Network effects service package."""

import importlib.util
import sys
from pathlib import Path


def _load_module(module_name: str, file_name: str):
    module_path = Path(__file__).resolve().parent / file_name
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module: {file_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_models = _load_module("network_effects_models_init", "models.py")
_service = _load_module("network_effects_service_init", "service.py")

BenchmarkSummary = _models.BenchmarkSummary
TeacherScore = _models.TeacherScore
TeacherSignal = _models.TeacherSignal
NetworkEffectsService = _service.NetworkEffectsService

__all__ = ["NetworkEffectsService", "TeacherSignal", "TeacherScore", "BenchmarkSummary"]
