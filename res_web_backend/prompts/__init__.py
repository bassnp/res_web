# Prompts module for the Portfolio Backend API
# Contains system prompts for AI agents

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_fit_check_prompt() -> str:
    """Load the fit check system prompt."""
    prompt_path = PROMPTS_DIR / "fit_check_system.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
