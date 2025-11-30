"""File operations confined to the working directory."""

from __future__ import annotations

import os
from typing import List

from app.state import AppState


def ensure_work_dir(state: AppState) -> None:
    """Ensure the working directory exists."""
    os.makedirs(state.work_dir, exist_ok=True)


def safe_path(state: AppState, filename: str) -> str:
    """Restrict the path to the working directory using only the basename."""
    basename = os.path.basename(filename)
    return os.path.join(state.work_dir, basename)


def list_files_raw(state: AppState) -> List[str]:
    """Return only regular file names within the working directory."""
    ensure_work_dir(state)
    entries: List[str] = []
    for name in os.listdir(state.work_dir):
        full = os.path.join(state.work_dir, name)
        if os.path.isfile(full):
            entries.append(name)
    return sorted(entries)


def list_files(state: AppState) -> str:
    """List all regular files within the working directory."""
    files = list_files_raw(state)
    if not files:
        return f"No files found in '{state.work_dir}'."
    return "Files in the working directory:\n" + "\n".join(files)


def read_file(state: AppState, filename: str) -> str:
    """Read a text file within the working directory."""
    path = safe_path(state, filename)
    if not os.path.exists(path):
        available = list_files_raw(state)
        available_str = ", ".join(available) if available else "no files available"
        return (
            f"Error: file '{filename}' not found in {state.work_dir}. "
            f"Available files: {available_str}."
        )
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        return f"Error: file '{filename}' does not appear to be readable text (encoding issue)."


def write_file(state: AppState, filename: str, content: str, overwrite: bool = False) -> str:
    """Create or overwrite a text file."""
    ensure_work_dir(state)
    path = safe_path(state, filename)

    if os.path.exists(path) and not overwrite:
        return (
            f"Error: file '{filename}' already exists in {state.work_dir}. "
            f"Set overwrite=true to replace it."
        )

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

    return f"File '{filename}' saved successfully in {state.work_dir}."


def append_to_file(state: AppState, filename: str, content: str) -> str:
    """Append content to the end of an existing text file."""
    path = safe_path(state, filename)
    if not os.path.exists(path):
        return f"Error: file '{filename}' not found in {state.work_dir}."
    with open(path, "a", encoding="utf-8") as file:
        file.write("\n" + content)
    return f"Content appended to file '{filename}'."


def delete_file(state: AppState, filename: str) -> str:
    """Remove a file from the working directory."""
    path = safe_path(state, filename)
    if not os.path.exists(path):
        return f"Error: file '{filename}' not found in {state.work_dir}."
    os.remove(path)
    return f"File '{filename}' removed from {state.work_dir}."


def rename_file(state: AppState, old_name: str, new_name: str) -> str:
    """Rename a file within the working directory."""
    old_path = safe_path(state, old_name)
    new_path = safe_path(state, new_name)
    if not os.path.exists(old_path):
        return f"Error: file '{old_name}' not found in {state.work_dir}."
    if os.path.exists(new_path):
        return f"Error: a file named '{new_name}' already exists in {state.work_dir}."
    os.rename(old_path, new_path)
    return f"File renamed from '{old_name}' to '{new_name}'."


def search_in_files(state: AppState, term: str) -> str:
    """Search for a term (case-insensitive) across all text files in the directory."""
    term = term.strip()
    if not term:
        return "Error: empty search term."

    files = list_files_raw(state)
    if not files:
        return f"No files found in '{state.work_dir}'."

    term_lower = term.lower()
    results = []

    for name in files:
        path = safe_path(state, name)
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
        except UnicodeDecodeError:
            continue

        if term_lower not in content.lower():
            continue

        lines = content.splitlines()
        snippets = []
        for idx, line in enumerate(lines):
            if term_lower in line.lower():
                start = max(0, idx - 1)
                end = min(len(lines), idx + 2)
                snippet = "\n".join(lines[start:end])
                snippets.append(f"(Linha {idx + 1})\n{snippet}")
                if len(snippets) >= 3:
                    break
        results.append(f"Arquivo: {name}\n" + "\n---\n".join(snippets))

    if not results:
        return f"No occurrences of '{term}' found in the files in '{state.work_dir}'."

    return f"Results for '{term}':\n\n" + "\n\n====================\n\n".join(results)


def count_words(state: AppState, filename: str) -> str:
    """Count lines, words, and characters in a text file."""
    path = safe_path(state, filename)
    if not os.path.exists(path):
        return f"Error: file '{filename}' not found in {state.work_dir}."

    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
    except UnicodeDecodeError:
        return f"Error: file '{filename}' does not appear to be readable text."

    lines = content.splitlines()
    words = content.split()
    chars = len(content)

    return (
        f"Stats for '{filename}':\n"
        f"- Lines: {len(lines)}\n"
        f"- Words: {len(words)}\n"
        f"- Characters: {chars}"
    )


def read_file_chunk(state: AppState, filename: str, start_line: int = 1, num_lines: int = 50) -> str:
    """Read only a portion (lines) of a text file."""
    if start_line < 1:
        start_line = 1
    if num_lines <= 0:
        return "Error: num_lines must be > 0."

    path = safe_path(state, filename)
    if not os.path.exists(path):
        return f"Error: file '{filename}' not found in {state.work_dir}."

    try:
        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        return f"Error: file '{filename}' does not appear to be readable text."

    start_idx = start_line - 1
    end_idx = start_idx + num_lines
    chunk = lines[start_idx:end_idx]

    if not chunk:
        return f"No content in lines {start_line}-{start_line + num_lines - 1}."

    return (
        f"Lines {start_line}-{start_line + len(chunk) - 1} of '{filename}':\n"
        + "".join(chunk)
    )


__all__ = [
    "append_to_file",
    "count_words",
    "delete_file",
    "ensure_work_dir",
    "list_files",
    "list_files_raw",
    "read_file",
    "read_file_chunk",
    "rename_file",
    "search_in_files",
    "safe_path",
    "write_file",
]
