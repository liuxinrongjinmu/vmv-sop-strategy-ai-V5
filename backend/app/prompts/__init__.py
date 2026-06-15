"""Prompt模板管理模块"""
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(filename: str) -> str:
    """加载prompt模板文件"""
    prompt_path = PROMPTS_DIR / filename
    if prompt_path.exists():
        return prompt_path.read_text(encoding='utf-8')
    raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
