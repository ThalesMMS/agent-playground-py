"""Settings and shared client for the local agent."""

from openai import OpenAI

DEFAULT_BASE_URL = "http://localhost:1234/v1"
DEFAULT_API_KEY = "lm-studio"
DEFAULT_MODEL = "qwen/qwen3-4b-2507"
DEFAULT_WORK_DIR = "workspace"

client = OpenAI(base_url=DEFAULT_BASE_URL, api_key=DEFAULT_API_KEY)

__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_API_KEY",
    "DEFAULT_MODEL",
    "DEFAULT_WORK_DIR",
    "client",
]
