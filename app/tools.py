"""Tool definitions and dispatch to the corresponding operations."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from app.state import AppState
from app.context_store import append_context, read_context
from app import workdir


BASE_TOOLS: List[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in the current working directory.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full content of a text file in the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "File name (e.g., 'notes.txt').",
                    }
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a text file in the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "File name (e.g., 'new.txt').",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to save.",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "If true, overwrite if the file already exists.",
                    },
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_to_file",
            "description": "Append content to the end of an existing text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "File name.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Text to append.",
                    },
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Remove a file from the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to remove.",
                    }
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rename_file",
            "description": "Rename a file within the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_name": {
                        "type": "string",
                        "description": "Current file name.",
                    },
                    "new_name": {
                        "type": "string",
                        "description": "New file name.",
                    },
                },
                "required": ["old_name", "new_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_files",
            "description": "Search for a term in all text files in the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Term to search for (case-insensitive).",
                    }
                },
                "required": ["term"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_words",
            "description": "Count lines, words, and characters in a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "File name.",
                    }
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_chunk",
            "description": "Read only a portion (lines) of a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "File name.",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Starting line (1-based).",
                    },
                    "num_lines": {
                        "type": "integer",
                        "description": "Number of lines to read.",
                    },
                },
                "required": ["filename"],
            },
        },
    },
]

SPAWN_SUBAGENT_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "spawn_subagent",
        "description": (
            "Create a dedicated subagent to solve a specific subtask, "
            "calling this same program with --role=subagent and --once. "
            "Use it to split complex tasks into well-defined subtasks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Clear description of the subtask the subagent should execute.",
                }
            },
            "required": ["task"],
        },
    },
}


def get_tools_for_role(role: str) -> List[dict]:
    """Return the list of tools available for the given role."""
    if role == "main":
        return BASE_TOOLS + [SPAWN_SUBAGENT_TOOL]
    return BASE_TOOLS


def spawn_subagent(task: str, state: AppState) -> str:
    """Run this same program as a subagent to solve a subtask."""
    sid = state.next_subagent_id()
    concise_task = task.strip()
    if concise_task:
        concise_task = f"{concise_task} (Respond concisely: up to 120 words or 3-6 bullets.)"
    else:
        concise_task = "(Respond concisely: up to 120 words or 3-6 bullets.)"

    append_context(f"[spawn #{sid}] {concise_task}")

    print(f"\n[MAIN] -> [SUBAGENT #{sid}] Starting subagent for task:")
    print(f"        {concise_task}")

    script_path = Path(__file__).resolve().parent.parent / "main.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--role",
        "subagent",
        "--once",
        concise_task,
    ]

    completed = subprocess.run(cmd, capture_output=True, text=True)

    out = (completed.stdout or "").strip()
    err = (completed.stderr or "").strip()

    if completed.returncode != 0:
        print(f"[MAIN] <- [SUBAGENT #{sid}] ERROR (returncode={completed.returncode})")
        if err:
            print(f"[SUBAGENT #{sid} STDERR]\n{err}\n")
        return (
            f"[Error running subagent #{sid}] "
            f"returncode={completed.returncode}, stderr={err}"
        )

    print(f"[MAIN] <- [SUBAGENT #{sid}] Subagent response:\n{out}\n")

    if not out:
        out = f"[Subagent #{sid}] returned no output."

    trimmed_out = " ".join(out.split())[:600]
    append_context(f"[done #{sid}] {trimmed_out}")

    context_snapshot = read_context()

    return (
        "[Context snapshot]\n" + context_snapshot + "\n\n" + out
    )


def execute_tool(tool_name: str, raw_args: str, state: AppState, role: str) -> str:
    """Dispatch a model tool call to the corresponding Python function."""
    try:
        args: Dict[str, object] = json.loads(raw_args or "{}")
    except json.JSONDecodeError:
        args = {}

    if tool_name == "list_files":
        return workdir.list_files(state)
    if tool_name == "read_file":
        return workdir.read_file(state, args.get("filename", ""))
    if tool_name == "write_file":
        return workdir.write_file(
            state,
            args.get("filename", ""),
            args.get("content", ""),
            overwrite=bool(args.get("overwrite", False)),
        )
    if tool_name == "append_to_file":
        return workdir.append_to_file(state, args.get("filename", ""), args.get("content", ""))
    if tool_name == "delete_file":
        return workdir.delete_file(state, args.get("filename", ""))
    if tool_name == "rename_file":
        return workdir.rename_file(state, args.get("old_name", ""), args.get("new_name", ""))
    if tool_name == "search_in_files":
        return workdir.search_in_files(state, args.get("term", ""))
    if tool_name == "count_words":
        return workdir.count_words(state, args.get("filename", ""))
    if tool_name == "read_file_chunk":
        return workdir.read_file_chunk(
            state,
            args.get("filename", ""),
            start_line=int(args.get("start_line", 1) or 1),
            num_lines=int(args.get("num_lines", 50) or 50),
        )
    if tool_name == "spawn_subagent":
        if role != "main":
            return "Internal error: spawn_subagent must not be used in subagents."
        return spawn_subagent(args.get("task", ""), state)
    return f"Unknown tool: {tool_name}"


__all__ = [
    "BASE_TOOLS",
    "SPAWN_SUBAGENT_TOOL",
    "execute_tool",
    "get_tools_for_role",
    "spawn_subagent",
]
