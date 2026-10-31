import re
from typing import Dict, Optional
from services.log_service import logger
from ollama import chat
from config.prompt_config import PROMPT_TEMPLATES
from config.prompt_loader import get_prompt
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
from pathlib import Path
from fastapi.responses import FileResponse
# ========== 双语关键词配置 ==========

MOLD_KNOWLEDGE_ID = "mold_rules.md"

SPACE_MAP = [
    ("卫生间", {"bathroom", "toilet"}),
    ("厨房", {"kitchen"}),
    ("卧室", {"bedroom"}),
    ("客厅", {"living room", "lounge"}),
    ("书房", {"study"}),
    ("地下室", {"basement"}),
]

FIELD_KEYWORDS: Dict[str, set] = {
    "wall_info": {"wall", "walls", "mold", "stain", "water mark", "dirt", "墙面", "霉斑", "水渍"},
    "ceiling_info": {"ceiling", "top", "水渍", "霉斑", "stain"},
    "floor_info": {"floor", "ground", "water", "积水", "水渍"},
    "moisture_trace": {"droplet", "condensation", "水珠", "凝露"},
    "furniture_layout": {"furniture", "cabinet", "chair", "towel rack", "家具"},
    "window_info": {"window", "窗户"},
    "light_vent": {"light", "dark", "vent", "ventilation", "采光", "昏暗"},
    "clutter": {"clutter", "mess", "杂物"},
    "cleanliness": {"clean", "dirty", "干净", "脏污"},
    "other_detail": set()
}


def normalize_text(txt: str) -> str:
    txt = txt.lower()
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


def parse_moondream_text(raw: str) -> Dict:
    raw = normalize_text(raw)
    res = {
        "space_type": "其他",
        "furniture_layout": "未见",
        "bedding_status": "未见",
        "wall_info": "未见",
        "ceiling_info": "未见",
        "floor_info": "未见",
        "moisture_trace": "未见",
        "window_info": "未见",
        "light_vent": "未见",
        "clutter": "未见",
        "cleanliness": "未见",
        "other_detail": "未见"
    }
    # 空间类型 互斥单选
    for cn, words in SPACE_MAP:
        if any(w in raw for w in words):
            res["space_type"] = cn
            break

    for field, keywords in FIELD_KEYWORDS.items():
        # 关键词按长度降序：长词组优先
        kw_list = sorted(keywords, key=lambda x: len(x), reverse=True)
        hit = []
        consumed_indexes = set()
        for kw in kw_list:
            idx = raw.find(kw)
            if idx == -1:
                continue
            # 如果这个位置已经被更长词组占用，跳过，防止拆词组
            overlap = any(not (idx + len(kw) <= start or idx >= start + len(used_kw)) for (start, used_kw) in consumed_indexes)
            if overlap:
                continue
            hit.append(kw)
            consumed_indexes.add((idx, kw))
        if hit:
            hit = list(dict.fromkeys(hit))
            res[field] = " ".join(hit)
        else:
            res[field] = "未见"
    return res

class MoondreamService:
    # 和LLaVA对齐：analyze_mold_ visual
    async def analyze_mold_visual(self, img_b64: str):
        # 拉知识库
        # rule_text = await get_rag_knowledge(MOLD_KNOWLEDGE_ID)
        prompt = get_prompt("moondream_visual")
        logger.info("[MoondreamService] analyze_mold_visual prompt loaded")
        resp = chat(
            model="moondream",
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }],
            options={
                "temperature": 0.1,
                "top_p": 0.1,
                "seed": 42,
                "max_tokens": 512,
                "keepalive": "10m"
            }
        )
        logger.info("moondream raw resp: " + str(resp))
        raw_content = resp["message"]["content"]
        img_struct = parse_moondream_text(raw_content)
        # 附加原始归一化文本，用于后置词组判断
        img_struct["__raw_text__"] = normalize_text(raw_content)
        return {"code": 200, "data": img_struct}

    # 和LLaVA对齐：analyze_mold_full
    async def analyze_mold_full(self, img_b64: str, temperature: Optional[float] = None, humidity: Optional[float] = None):
        # 拉知识库
        # rule_text = await get_rag_knowledge(MOLD_KNOWLEDGE_ID)
        prompt = get_prompt("moondream_full", temperature=temperature, humidity=humidity)
        logger.info("[MoondreamService] analyze_mold_full prompt loaded")
        resp = chat(
            model="moondream",
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }],
            options={
                "temperature": 0.1,
                "top_p": 0.1,
                "seed": 42,
                "max_tokens": 512,
                "keepalive": "10m",
            }
        )
        raw_content = resp["message"]["content"]
        logger.info("moondream raw resp: " + str(resp))
        img_struct = parse_moondream_text(raw_content)
        # 附加原始归一化文本，用于后置词组判断
        img_struct["__raw_text__"] = normalize_text(raw_content)
        return {"code": 200, "data": img_struct}

moondream_service = MoondreamService()