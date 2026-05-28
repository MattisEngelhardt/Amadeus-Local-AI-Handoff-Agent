from typing import get_args

from amadeus.core.modes import MODES
from amadeus.core.tool_registry import TOOL_REGISTRY
from amadeus.models.tools import ToolName


def test_all_tools_have_contracts():
    expected_tools = get_args(ToolName)
    for t in expected_tools:
        assert t in TOOL_REGISTRY, f"Tool {t} missing in TOOL_REGISTRY"


def test_tool_contracts_have_valid_modes():
    for name, contract in TOOL_REGISTRY.items():
        assert contract.mode in MODES, f"Tool {name} has invalid mode {contract.mode}"
