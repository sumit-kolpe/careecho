import argparse
import json
from pathlib import Path

from .evaluate import evaluate
from .nlp import review
from .schema import Plan


def main():
    parser = argparse.ArgumentParser(description="CareEcho synthetic teach-back research prototype")
    commands = parser.add_subparsers(dest="command", required=True)
    assess = commands.add_parser("review", help="Review text against a structured care plan")
    assess.add_argument("--plan", required=True)
    assess.add_argument("--transcript", required=True)
    assess.add_argument("--engine", choices=["rules", "openai"], default="rules")
    assess.add_argument("--allow-cloud-synthetic", action="store_true")
    assess.add_argument("--model")
    asr = commands.add_parser("transcribe", help="Run local Whisper on a 16-bit PCM WAV")
    asr.add_argument("audio")
    asr.add_argument("--model", default="tiny.en")
    asr.add_argument("--glossary", default="")
    ev = commands.add_parser("evaluate")
    ev.add_argument("--data", default="data")
    for sub in [assess, asr, ev]:
        sub.add_argument("--output")
    args = parser.parse_args()
    try:
        if args.command == "review":
            plan = Plan.model_validate_json(Path(args.plan).read_text(encoding="utf-8"))
            transcript = Path(args.transcript).read_text(encoding="utf-8")
            if args.engine == "openai":
                from .llm import review_with_llm

                result = review_with_llm(
                    plan, transcript, consent=args.allow_cloud_synthetic, model=args.model
                )
            else:
                result = review(plan, transcript)
            result = result.model_dump()
        elif args.command == "transcribe":
            from .audio import transcribe

            result = transcribe(args.audio, args.model, args.glossary).model_dump()
        else:
            result = evaluate(args.data)
        rendered = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            path = Path(args.output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
    except (ValueError, OSError, RuntimeError, ImportError) as exc:
        parser.exit(2, f"CareEcho: {exc}\n")


if __name__ == "__main__":
    main()
