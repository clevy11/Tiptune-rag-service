"""Validate TipTune chat-training JSONL files without modifying them."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

VALID_ROLES = {"system", "user", "assistant"}
MOJIBAKE_MARKERS = ("Ã", "Â", "ðŸ", "â€")


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"{path}:{line_number}: invalid JSON ({error.msg})")
            continue

        messages = record.get("messages")
        if not isinstance(messages, list) or len(messages) < 2:
            errors.append(f"{path}:{line_number}: messages must be a list with at least two items")
            continue
        if messages[0].get("role") != "system":
            errors.append(f"{path}:{line_number}: first message must have role 'system'")
        if messages[-1].get("role") != "assistant":
            errors.append(f"{path}:{line_number}: final message must have role 'assistant'")

        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                errors.append(f"{path}:{line_number}: message {index} is not an object")
                continue
            if message.get("role") not in VALID_ROLES:
                errors.append(f"{path}:{line_number}: message {index} has an invalid role")
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                errors.append(f"{path}:{line_number}: message {index} has empty/non-text content")
            elif any(marker in content for marker in MOJIBAKE_MARKERS):
                errors.append(
                    f"{path}:{line_number}: message {index} appears to contain mojibake; "
                    "repair the original text before training"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    errors = [error for path in args.files for error in validate_file(path)]
    if errors:
        print("Dataset validation failed:")
        print("\n".join(errors))
        return 1
    print("Dataset validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
