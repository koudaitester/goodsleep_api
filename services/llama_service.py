from asyncio import log
import datetime

import httpx
import json
from ollama import chat
from services.log_service import logger
import os
import re
from config.settings import settings
from config.prompt_config import PROMPT_TEMPLATES
from typing import Dict
from pydantic import BaseSettings, Field, PostgresDsn, validator
from config.settings import Settings
from config.prompt_loader import get_prompt

# 霉菌知识库标识
MOLD_KNOWLEDGE_ID = "mold_rules.md"

DISCLAIMER = """
【免责声明】本评估仅为AI参考判断，不能替代专业检测机构。
若怀疑存在严重霉菌污染，请联系专业机构上门检测。
"""

class LlamaService:
    def __init__(self, model_name="llava"):
        self.model_name = model_name
        self.ollama_url = settings.OLLAMA_BASE_URL + "/api/generate"

    async def call_llama(self, prompt: str, image_b64: str|None = None):
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_b64] if image_b64 else [],
            "stream": False,
            "format": "json"
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(self.ollama_url, json=payload)
                logger.info("ollama raw resp: " + resp.text)
                data = resp.json()
                if "response" not in data:
                    raise KeyError("missing response")
                return json.loads(data["response"])
        except Exception as e:
            logger.error("大模型调用异常：", e)
            # 降级mock
            return {
                "risk_level": "medium",
                "summary": "模型调用失败，使用兜底评估",
                "suggestions": ["检查ollama服务是否正常运行，模型是否拉取成功"]
            }

    # ========== 移入类内 ==========
    async def analyze_mold_visual(self, img_b64: str):
        # Service：只拉知识库 + 拼接prompt + 调用大模型
        # rule_text = await get_rag_knowledge(MOLD_KNOWLEDGE_ID)
        prompt = get_prompt("mold_vision_extract_llava")
        #压缩base64图片
        # img_b64 = resize_image_for_llava(img_b64, 1000)

        # logger.info("prompt: "  ￥+ prompt)
        resp = chat(
            model="llava",
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }],
            options={
            "temperature": 0.0,
            "top_p": 0.1,
            "seed": 42,
            "max_tokens": 384,
            "keepalive": "10m"
            }
        )
        logger.info("llava resp: " + str(resp))
        return {"code": 200, "data": resp["message"]["content"]}

    async def analyze_mold_full(self, img_b64: str, temperature: float|None = None, humidity: float|None = None):
        # Service：接收b64、温湿度，拉规则，拼接prompt，调用模型
        # rule_text = await get_rag_knowledge(MOLD_KNOWLEDGE_ID)
        # if temperature is None or humidity is None:
        #     raise ValueError("温湿度参数不能为空")

        prompt = get_prompt("mold_vision_extract_llava")
        logger.info("prompt: " + prompt)

        resp = chat(
            model="llava",
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
        return {"code": 200, "data": resp["message"]["content"]}

llama_service = LlamaService()