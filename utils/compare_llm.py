import requests
import time
from typing import List

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# 模型分组
TEXT_MODELS: List[str] = [
    "qwen2.5:7b"
]

VISION_MODELS: List[str] = [
    "llava15:latest",
    "llava:7b-v1.5-q4_K_M",
    "llava:7b",
    "llava:latest",
    "llama3.2-vision:latest",
    "moondream:latest",
    "moondream:v2"
]

# 在这里切换任务类型："text" / "vision"
TASK_TYPE = "text"
PROMPT_TEXT = "简要说明什么是贝叶斯网络，适合工程做风险评估的要点"
# 视觉任务示例prompt，跑看图时再启用
PROMPT_VISION = "详细描述这张图片里的内容，重点识别环境里的潮湿、霉菌痕迹"

def run_one(model_name: str, prompt: str, image_base64=None):
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    if image_base64:
        payload["images"] = [image_base64]
    start = time.perf_counter()
    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
    cost = time.perf_counter() - start
    if resp.status_code == 200:
        return cost, resp.json()["response"]
    else:
        return cost, f"[HTTP ERROR {resp.status_code}] {resp.text}"

if __name__ == "__main__":
    if TASK_TYPE == "text":
        run_list = TEXT_MODELS
        prompt = PROMPT_TEXT
        print("=== 【纯文本推理任务】===")
    else:
        run_list = VISION_MODELS
        prompt = PROMPT_VISION
        print("=== 【视觉图文任务】===")

    for m in run_list:
        print(f"\n===== MODEL: {m} =====")
        t, res = run_one(m, prompt)
        print(f"耗时：{t:.2f} s")
        print(res)
