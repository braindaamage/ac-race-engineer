"""Test configuration for telemetry capture tests.

Sets up sys.path so that AC app modules can be imported in the test environment,
and injects mock ac/acsys modules into sys.modules before any test imports.
"""
import sys
import os

# Add AC app paths to sys.path for module imports
_app_root = os.path.join(os.path.dirname(__file__), "..", "..", "ac_app", "ac_race_engineer")
_app_root = os.path.normpath(_app_root)
_modules_root = os.path.join(_app_root, "modules")

for _path in [_app_root, _modules_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Inject mock ac and acsys modules BEFORE any test imports
_tests_dir = os.path.dirname(__file__)
if _tests_dir not in sys.path:
    sys.path.insert(0, _tests_dir)

from mocks import ac as _mock_ac
from mocks import acsys as _mock_acsys

sys.modules["ac"] = _mock_ac
sys.modules["acsys"] = _mock_acsys
