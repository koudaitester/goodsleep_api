# config/prompt_config.py
from typing import Dict

PROMPT_TEMPLATES: Dict[str, str] = {
    "moondream_visual": """

  You are an image observer. Describe everything you can see in this bedroom image in maximum detail.
Pay special attention to sleep-environment related details: window, curtain, bed placement, bedding, electronics near bed, clutter, dust, light sources, damp marks, water stains, mold spots.
Be thorough, do not omit any visible details. Describe objectively. Write as long and complete a description as you can.


"""
}
