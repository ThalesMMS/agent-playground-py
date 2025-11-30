"""Core interaction with the model, executing tool calls and handling responses."""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

from app.config import DEFAULT_MODEL, client
from app.state import AppState
from app.tools import execute_tool, get_tools_for_role


# Safety limits to prevent infinite tool-call loops.
MAX_TOOL_ROUNDS = 12
MAX_REPEAT_SIGNATURES = 3
MAX_CONSECUTIVE_MISSING_FILES = 3


def _finalize_without_tools(messages: List[Dict]) -> str:
    """Ask the model for a final response without allowing further tool calls."""

    guidance = (
        "Finalize your response to the user now, without calling tools. "
        "Use only the context already available and the subagents' answers. "
        "Be concise."
    )

    messages.append({"role": "system", "content": guidance})

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
        tool_choice="none",
    )

    final_msg = response.choices[0].message
    final_content = final_msg.content or guidance
    messages.append({"role": "assistant", "content": final_content})
    return final_content


def _signature_from_tool_calls(tool_calls) -> Optional[Tuple[Tuple[str, str], ...]]:
    """Extract a signature (tool, normalized args) for loop detection."""

    if not tool_calls:
        return None

    try:
        signature: List[Tuple[str, str]] = []
        for call in tool_calls:
            name = call.function.name
            raw_args = call.function.arguments or ""
            try:
                parsed = json.loads(raw_args)
                normalized = json.dumps(parsed, sort_keys=True)
            except Exception:
                normalized = str(raw_args)
            signature.append((name, normalized))
        return tuple(signature)
    except Exception:
        return None


def step_with_tools(messages: List[Dict], role: str, state: AppState) -> str:
    """Run an interaction round with tool calls until obtaining a final answer.

    Includes basic guard rails to avoid infinite loops: it limits the number of
    tool-call rounds and stops if the same call signature repeats too many times.
    """
    tools = get_tools_for_role(role)
    rounds = 0
    last_signature: Optional[Tuple[Tuple[str, str], ...]] = None
    repeat_count = 0
    consecutive_missing_files = 0

    while True:
        if rounds >= MAX_TOOL_ROUNDS:
            warning = (
                "Stopped using tools: call limit reached. "
                "Refine the instruction or adjust the agent code if you need more iterations."
            )
            messages.append({"role": "assistant", "content": warning})
            return warning

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        rounds += 1

        message = response.choices[0].message

        if state.show_debug:
            print(f"\n[DEBUG {role.upper()}] Raw response (before tools):")
            print(f"  content: {repr(message.content)}")
            if message.tool_calls:
                print("  tool_calls:")
                for call in message.tool_calls:
                    print(f"    - id: {call.id}")
                    print(f"      name: {call.function.name}")
                    print(f"      arguments (JSON): {call.function.arguments}")

        if not message.tool_calls:
            final_content = message.content or ""
            messages.append({"role": "assistant", "content": final_content})
            return final_content

        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": message.tool_calls,
            }
        )

        signature = _signature_from_tool_calls(message.tool_calls)
        if signature and signature == last_signature:
            repeat_count += 1
        else:
            repeat_count = 0
            last_signature = signature

        if repeat_count >= MAX_REPEAT_SIGNATURES:
            return _finalize_without_tools(messages)

        for call in message.tool_calls:
            tool_name = call.function.name
            raw_args = call.function.arguments or "{}"
            result = execute_tool(tool_name, raw_args, state, role)

            if "not found" in result.lower() and "file" in result.lower():
                consecutive_missing_files += 1
            else:
                consecutive_missing_files = 0

            if consecutive_missing_files >= MAX_CONSECUTIVE_MISSING_FILES:
                return _finalize_without_tools(messages)

            if state.show_debug:
                print(f"\n[DEBUG {role.upper()}] Executing tool '{tool_name}' with args = {raw_args}")
                print("[DEBUG] Result (first 300 chars):")
                preview = result[:300]
                print(preview + ("..." if len(result) > 300 else ""))

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )


__all__ = ["step_with_tools"]
