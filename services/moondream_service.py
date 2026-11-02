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
import time
# ========== 双语关键词配置 ==========

MOLD_KNOWLEDGE_ID = "mold_rules.md"

from typing import Dict

SPACE_MAP = [
    ("卧室", ["bedroom"]),
    ("其他", [])
]

FIELD_KEYWORDS = {
    "air_hint": ["not observed"],
    "mold_moisture": ["mold spots", "mold", "water stain", "water stains", "damp"],
    "vent_condition": ["window open", "window closed", "window is open", "window is closed"],
    "furniture_layout": ["bed against wall", "bed in the center", "narrow passage"],
    "electronics": ["phone", "charger", "lamp", "nightstand lamp"],
    "bed_occlusion": ["bed blocked"],
    "bedding_status": ["piled bedding"],
    "clutter_level": ["disarray", "scattered items", "scattered around the bed", "cluttered"],
    "dust_accumulation": ["dust"],
    "window_curtain": ["curtain", "curtain drawn", "drawn over window", "thick curtain", "thin curtain", "light leakage"],
    "light_source": ["light sources", "lamp shine on bed"],
    "wall_ceiling": ["water stain", "water stains", "peeling"],
    "odor_cue": ["mold spots", "moisture"],
    "furniture_layout": ["bed against wall", "bed in the center", "narrow passage", "bed positioned against the wall", "bed is positioned against the wall"],
    "bedding_status": ["piled bedding", "rumpled"]
}

def normalize_text(txt: str) -> str:
    txt = txt.lower()
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

def parse_moondream_text(raw: str) -> Dict:
    raw = normalize_text(raw)
    res = {
        "air_hint": "未见",
        "mold_moisture": "未见",
        "vent_condition": "未见",
        "furniture_layout": "未见",
        "electronics": "未见",
        "bed_occlusion": "未见",
        "bedding_status": "未见",
        "mattress_situation": "未见",
        "clutter_level": "未见",
        "dust_accumulation": "未见",
        "window_curtain": "未见",
        "light_source": "未见",
        "wall_ceiling": "未见",
        "odor_cue": "未见"
    }
    # 空间类型
    space_found = "其他"
    for cn, words in SPACE_MAP:
        if any(w in raw for w in words):
            space_found = cn
            break
    res["space_type"] = space_found

    for field, keywords in FIELD_KEYWORDS.items():
        kw_list = sorted(keywords, key=lambda x: len(x), reverse=True)
        hit = []
        consumed = []  # (start, end)
        for kw in kw_list:
            idx = raw.find(kw)
            if idx == -1:
                continue
            end = idx + len(kw)
            # 判断区间重叠
            overlap = False
            for s, e in consumed:
                if not (end <= s or idx >= e):
                    overlap = True
                    break
            if overlap:
                continue
            hit.append(kw)
            consumed.append((idx, end))
        if hit:
            hit = list(dict.fromkeys(hit))
            res[field] = " ".join(hit)
        else:
            res[field] = "未见"
    return res


class MoondreamService:
    async def analyze_sleep_visual(self, img_b64: str):
        # 获取用于视觉分析的提示词
        start_ts = time.time()
        prompt = get_prompt("moondream_visual")
        logger.info("[MoondreamService] analyze_sleep_visual prompt loaded")
        # 调用moondream模型进行图像分析
        resp = chat(
            model="moondream",
            messages=[{
                "role": "user",
                "content": prompt,  # 使用获取的提示词
                "images": [img_b64]  # 传入base64编码的图像
            }],
            options={
                "temperature":0.2,      # 控制输出的随机性，值越小越确定
                "top_p":0.2,           # 控制词核采样，值越小选择概率越高的词
                "seed":42,             # 随机种子，确保结果可复现
                "max_tokens":1024,     # 限制最大输出token数量
                "keepalive":"10m"      # 保持连接时间10分钟
            }
        )
        # 记录原始响应日志
        logger.info("[MoondreamService] sleep moondream raw resp: " + str(resp))
        # 解析模型返回的内容并添加规范化文本
        cost = round(time.time() - start_ts, 2)
        raw_content = resp["message"]["content"]
        img_struct = parse_moondream_text(raw_content)
        img_struct["__raw_text__"] = normalize_text(raw_content)
        img_struct["infer_cost_sec"] = cost
        # 返回处理后的结果，状态码200表示成功
        return {"code": 200, "data": img_struct}

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