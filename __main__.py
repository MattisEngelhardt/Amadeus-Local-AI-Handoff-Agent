import argparse
import sys
from pathlib import Path

from amadeus.core.analyzer import TranscriptAnalyzer
from amadeus.core.cli import (
    run_add_command,
    run_archive_command,
    run_build_command,
    run_gaps_command,
    run_inbox_command,
    run_materials_command,
    run_new_command,
    run_open_command,
    run_projects_command,
    run_status_command,
    run_transcribe_command,
    run_use_command,
    run_validate_command,
)
from amadeus.core.ollama_client import OllamaClient, OllamaUnavailable
from amadeus.core.validator import RequirementsValidator
from amadeus.core.workflow import prepare_handoff_workspace


def _print_install_commands() -> None:
    print("Install and model setup commands:")
    print("1. Install Ollama for Windows from https://ollama.com/download")
    print("2. Open a new PowerShell window")
    print("3. ollama pull gemma4:e4b")
    print("4. ollama create amadeus -f amadeus/Modelfile")
    print("5. python -m amadeus check-runtime")


def check_runtime(args: argparse.Namespace) -> int:
    client = OllamaClient(base_url=args.ollama_url, timeout=args.timeout)
    print("Amadeus runtime check")
    print(f"Ollama URL: {args.ollama_url}")

    try:
        models = client.list_models()
    except OllamaUnavailable as exc:
        print(f"FAIL: Ollama is not reachable: {exc}")
        _print_install_commands()
        return 2

    print("OK: Ollama is reachable")
    for model in (args.base_model, args.agent_model):
        if model in models:
            print(f"OK: model present: {model}")
        else:
            print(f"MISSING: model not present: {model}")

    if args.base_model not in models:
        print(f"Run: ollama pull {args.base_model}")
        return 3

    if args.agent_model not in models:
        print(f"Run: ollama create {args.agent_model} -f amadeus/Modelfile")
        return 4

    sample = client.generate(
        prompt="Reply with exactly: Amadeus ready.",
        model=args.agent_model,
        system="You are Amadeus. Follow the user instruction exactly.",
        options={"temperature": 0},
    )
    print(f"OK: model response: {sample.strip()}")
    return 0


def build_text(args: argparse.Namespace) -> int:
    analyzer = TranscriptAnalyzer(model=args.model, ollama_base_url=args.ollama_url)
    requirements = analyzer.analyze(args.text)
    if requirements is None:
        print("FAIL: Amadeus could not analyze the input. Check Ollama and the model first.")
        return 2

    if args.project_name:
        requirements.project_name = args.project_name

    validator = RequirementsValidator()
    requirements = validator.validate(args.text, requirements)
    result = prepare_handoff_workspace(
        requirements,
        raw_text=args.text,
        output_dir=args.output_dir,
        approve_readiness=args.approve_readiness,
        approval_note=args.approval_note,
        channel="cli",
        input_kind="text",
        source_files=args.materials,
    )

    if result.blocked:
        print("BLOCKED: Readiness gate found open blockers.")
        print(f"Readiness score: {result.state.readiness.score}/100")
        for blocker in result.state.open_blockers():
            print(f"- {blocker.title}: {blocker.question}")
        print(f"Review package written: {result.project_path}")
        print("Rerun with --approve-readiness and --approval-note to waive blockers.")
        return 4

    if not result.built:
        print(f"FAIL: {result.message}")
        return 3

    print(f"OK: Handoff workspace created: {result.project_path}")
    print(f"Readiness score: {result.state.readiness.score}/100")
    print(f"State saved: {result.state_path}")
    print("Start there by reading CLAUDE.md and AGENTS.md.")
    return 0


def run_eval_command(args) -> int:
    from amadeus.evals.runner import run_eval_suite

    report = run_eval_suite(mode=args.mode, case_ids=args.case)
    return 0 if report.cases_failed == 0 else 1


def run_agent_command(args) -> int:
    from pathlib import Path

    from amadeus.core.agent_loop import AgentLoop
    from amadeus.core.ollama_client import OllamaClient
    from amadeus.core.project_registry import ProjectRegistry
    from amadeus.core.state_store import ProjectStateStore

    registry = ProjectRegistry()
    entry = registry.get_active()

    # Simple fallback: if no project, create one or fail
    if not entry:
        print("No active project. Please run 'amadeus new' first.")
        return 1

    store = ProjectStateStore()
    state = store.load(Path(entry.project_path))
    client = OllamaClient(base_url=args.ollama_url)

    loop = AgentLoop(
        state=state,
        project_path=Path(entry.project_path),
        client=client,
        model=args.model,
        dry_run=args.dry_run,
    )

    print(f"Starting Agent Loop for {state.project_name} in mode {loop.current_mode}...")
    final_state = loop.run(initial_text=args.text)

    store.save(final_state, Path(entry.project_path))
    registry.update_state(final_state.project_name, final_state)

    print("Agent loop finished.")
    print("Action Log summary:")
    for action in loop.action_log:
        success_marker = "OK" if action.result.success else "FAIL"
        print(f"  [{action.step}] {action.decision.action.tool} -> {success_marker}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m amadeus",
        description="Amadeus local Gemma/Ollama handoff agent.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install-commands")
    install_parser.set_defaults(func=lambda _args: _print_install_commands() or 0)

    check_parser = subparsers.add_parser("check-runtime")
    check_parser.add_argument("--ollama-url", default="http://localhost:11434")
    check_parser.add_argument("--base-model", default="gemma4:e4b")
    check_parser.add_argument("--agent-model", default="amadeus")
    check_parser.add_argument("--timeout", type=float, default=120.0)
    check_parser.set_defaults(func=check_runtime)

    build_parser = subparsers.add_parser("build-text")
    build_parser.add_argument("--text", required=True)
    build_parser.add_argument("--output-dir", default="./output")
    build_parser.add_argument("--project-name", default="")
    build_parser.add_argument("--model", default="amadeus")
    build_parser.add_argument("--ollama-url", default="http://localhost:11434")
    build_parser.add_argument(
        "--approve-readiness",
        action="store_true",
        help="Allow build with documented readiness blockers waived.",
    )
    build_parser.add_argument(
        "--approval-note",
        default="",
        help="Required rationale when waiving readiness blockers.",
    )
    build_parser.add_argument(
        "--materials",
        nargs="*",
        default=[],
        type=Path,
        help="Source files to ingest",
    )
    build_parser.set_defaults(func=build_text)

    eval_parser = subparsers.add_parser("eval")
    eval_parser.add_argument(
        "--mode", choices=["deterministic", "local_model"], default="deterministic"
    )
    eval_parser.add_argument("--case", nargs="*", default=None)
    eval_parser.set_defaults(func=run_eval_command)

    new_parser = subparsers.add_parser("new")
    new_parser.add_argument("text")
    new_parser.add_argument("--model", default="amadeus")
    new_parser.add_argument("--ollama-url", default="http://localhost:11434")
    new_parser.add_argument("--output-dir", default="")
    new_parser.set_defaults(func=run_new_command)

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("files", nargs="+")
    add_parser.set_defaults(func=run_add_command)

    status_parser = subparsers.add_parser("status")
    status_parser.set_defaults(func=run_status_command)

    gaps_parser = subparsers.add_parser("gaps")
    gaps_parser.set_defaults(func=run_gaps_command)

    materials_parser = subparsers.add_parser("materials")
    materials_parser.set_defaults(func=run_materials_command)

    build_cmd_parser = subparsers.add_parser("build")
    build_cmd_parser.add_argument("--approve-readiness", action="store_true")
    build_cmd_parser.add_argument("--approval-note", default="")
    build_cmd_parser.set_defaults(func=run_build_command)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.set_defaults(func=run_validate_command)

    projects_parser = subparsers.add_parser("projects")
    projects_parser.set_defaults(func=run_projects_command)

    use_parser = subparsers.add_parser("use")
    use_parser.add_argument("project_name")
    use_parser.set_defaults(func=run_use_command)

    open_parser = subparsers.add_parser("open")
    open_parser.set_defaults(func=run_open_command)

    archive_parser = subparsers.add_parser("archive")
    archive_parser.add_argument("project_name")
    archive_parser.set_defaults(func=run_archive_command)

    inbox_parser = subparsers.add_parser("inbox")
    inbox_parser.set_defaults(func=run_inbox_command)

    transcribe_parser = subparsers.add_parser("transcribe")
    transcribe_parser.add_argument("audio_file")
    transcribe_parser.add_argument("--model-size", default="large-v3")
    transcribe_parser.add_argument("--language", default="de")
    transcribe_parser.set_defaults(func=run_transcribe_command)

    agent_parser = subparsers.add_parser("agent")
    agent_parser.add_argument("text", nargs="?", default="")
    agent_parser.add_argument("--dry-run", action="store_true")
    agent_parser.add_argument("--max-steps", type=int, default=20)
    agent_parser.add_argument("--model", default="amadeus")
    agent_parser.add_argument("--output-dir", default="")
    agent_parser.add_argument("--ollama-url", default="http://localhost:11434")
    agent_parser.set_defaults(func=run_agent_command)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
