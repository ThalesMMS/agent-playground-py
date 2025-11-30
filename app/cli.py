"""Command-line interface layer for the local agent."""

from __future__ import annotations

import argparse
import sys
from typing import Dict, List, Optional

from app.agent import step_with_tools
from app.context_store import clear_context
from app.prompts import build_system_message
from app.state import AppState
from app.config import DEFAULT_WORK_DIR


def chat_loop(role: str, state: AppState, initial_user_message: Optional[str] = None) -> None:
    messages: List[Dict] = [build_system_message(role)]

    if role == "main":
        print(f"[MAIN] Main agent started. work_dir='{state.work_dir}'")
    else:
        print(f"[SUBAGENT] Started in interactive mode. work_dir='{state.work_dir}'")

    if initial_user_message:
        messages.append({"role": "user", "content": initial_user_message})
        answer = step_with_tools(messages, role, state)
        print(f"\n{role.capitalize()}:\n{answer}")

    print("\n--- Interactive chat mode (Ctrl+C to exit) ---")
    try:
        while True:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            messages.append({"role": "user", "content": user_input})
            answer = step_with_tools(messages, role, state)
            print(f"\n{role.capitalize()}: {answer}")
    except KeyboardInterrupt:
        print("\n\nClosing chat. See you later!")
        sys.exit(0)


def single_turn(role: str, message: str, state: AppState) -> None:
    messages: List[Dict] = [build_system_message(role), {"role": "user", "content": message}]
    answer = step_with_tools(messages, role, state)
    print(answer)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Local agent using openai/gpt-oss-20b via LM Studio, "
            "with generic file tools and subagent support."
        )
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Initial message for the agent (optional).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run only one question/answer round and exit.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show detailed tool logs (tool_calls, arguments, results).",
    )
    parser.add_argument(
        "--role",
        choices=["main", "subagent"],
        default="main",
        help="Define the role of this process: 'main' (main agent) or 'subagent'.",
    )
    parser.add_argument(
        "--work-dir",
        default=DEFAULT_WORK_DIR,
        help="Working directory for file operations (default: ./workspace).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Zera o contexto compartilhado no início de cada execução do agente principal.
    if args.role == "main":
        clear_context()

    state = AppState(work_dir=args.work_dir, show_debug=args.debug)

    if args.once:
        if not args.message:
            print("Error: to use --once you must provide an initial message.")
            print('Example: python3 main.py --once "Summarize the content of all files"')
            sys.exit(1)
        single_turn(args.role, args.message, state)
    else:
        chat_loop(args.role, state, args.message)


__all__ = ["main", "parse_args", "chat_loop", "single_turn"]


if __name__ == "__main__":
    main()
