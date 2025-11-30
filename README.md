# Local Agent (LM Studio / OpenAI API)

This project is a modular CLI-based agent designed to interact with local Large Language Models (LLMs) via LM Studio or any OpenAI-compatible API. It provides a sandboxed environment for file manipulation and supports a "sub-agent" system to break down complex tasks.

## Features

*   **Sandboxed File System:** All file operations are strictly confined to a specific working directory (default: `workspace/`) to ensure safety.
*   **Sub-agent System:** The main agent can spawn specialized sub-agents to handle subtasks. These sub-agents run as separate processes and return their results to the main context.
*   **Interactive & One-Shot Modes:** Run continuous chat sessions or execute single commands directly from the terminal.
*   **Context Management:** Automatically logs and manages context between the main agent and its sub-agents.
*   **Loop Protection:** Built-in guardrails to prevent infinite tool loops or repetitive actions.

## Prerequisites

*   **Python 3.10+**
*   **LM Studio** (or a compatible OpenAI API server) running locally.
    *   Default endpoint: `http://localhost:1234/v1`
    *   Default model identifier: `qwen/qwen3-4b-2507` (configurable)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Set up a virtual environment (recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install openai
    ```

## Usage

The entry point for the application is `main.py`.

### Interactive Mode
Starts a chat session where you can give instructions to the agent. It will use tools as needed and report back.
```bash
python main.py
```
*   *Note:* By default, this uses the `workspace` directory.

### Single Command (One-Shot)
Execute a specific instruction and exit immediately after the response.
```bash
python main.py --once "List all files in the workspace and summarize 'notes.txt'"
```

### Debug Mode
Use the `--debug` flag to view detailed logs of tool calls, arguments, and raw API responses. This is useful for understanding the agent's "thought process."
```bash
python main.py --debug
```

### Custom Working Directory
Specify a different directory for the agent to operate in.
```bash
python main.py --work-dir ./my-safe-folder
```

## Architecture Overview

The project is structured for modularity and clarity:

*   **`main.py`**: The entry point that handles argument parsing and initializes the application.
*   **`app/agent.py`**: Manages the interaction loop with the LLM, handling tool execution and enforcing safety limits.
*   **`app/tools.py`**: Defines the available tools (file operations, sub-agent spawning) and handles their dispatch.
*   **`app/workdir.py`**: Implements safe file operations, ensuring the agent cannot access files outside the designated workspace.
*   **`app/context_store.py`**: Manages a shared context file (`.context/context.txt`) to persist information across sub-agent calls.
*   **`app/config.py`**: Contains configuration defaults (API base URL, model name, etc.).

## Configuration

Default settings are defined in `app/config.py`. You can modify this file to change:
*   `DEFAULT_BASE_URL`: The address of your local LLM server.
*   `DEFAULT_MODEL`: The model identifier string expected by the server.
*   `DEFAULT_WORK_DIR`: The default folder for file operations.

## Safety Mechanisms

*   **Path Confinement:** The `safe_path` function in `app/workdir.py` ensures that all file paths are resolved relative to the workspace, blocking directory traversal attacks (e.g., `../`).
*   **Execution Limits:** `app/agent.py` enforces `MAX_TOOL_ROUNDS` (default: 12) and `MAX_REPEAT_SIGNATURES` (default: 3) to prevent the agent from getting stuck in loops.