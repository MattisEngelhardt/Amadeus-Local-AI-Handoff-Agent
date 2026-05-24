import argparse
import sys

from amadeus.core.analyzer import TranscriptAnalyzer
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m amadeus",
        description="Amadeus local Gemma/Ollama handoff agent.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install-commands")
    install_parser.set_defaults(func=lambda _args: (_print_install_commands() or 0))

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
    build_parser.set_defaults(func=build_text)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
