from amadeus.core.modes import MODES
from amadeus.core.tool_registry import TOOL_REGISTRY


def test_all_modes_have_system_prompts():
    for name, mode in MODES.items():
        assert mode.system_prompt.strip() != ""


def test_all_modes_reference_valid_tools():
    for name, mode in MODES.items():
        for t in mode.allowed_tools:
            assert t in TOOL_REGISTRY, f"Mode {name} uses unknown tool {t}"


def test_mode_system_prompts_contain_constitution():
    for name, mode in MODES.items():
        assert "Agent Constitution:" in mode.system_prompt
        assert "Never build before context is complete" in mode.system_prompt
