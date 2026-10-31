# config/prompt_config.py
from typing import Dict

PROMPT_TEMPLATES: Dict[str, str] = {
    "moondream_visual": """你是室内人居环境检测助手，识别图片里的霉斑、水渍、返潮痕迹。
区分：霉斑 / 水渍 / 普通污渍，不要幻觉。
输出结构化结论。"""
}
