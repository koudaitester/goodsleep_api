# utils/knowledge_loader.py
import os
from typing import Dict

KNOWLEDGE_DIR = "knowledge"


def load_knowledge_file(file_name: str) -> str:
    """读取 knowledge 下单个md文件，不带后缀或者带.md都可以"""
    if not file_name.endswith(".md"):
        file_name = f"{file_name}.md"
    fp = os.path.join(KNOWLEDGE_DIR, file_name)
    if not os.path.exists(fp):
        raise FileNotFoundError(f"知识库文件不存在：{file_name}")
    with open(fp, "r", encoding="utf-8") as f:
        return f.read()


def load_all_knowledge() -> Dict[str, str]:
    """一次性加载全部md，key为文件名（去掉.md后缀）"""
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    res = {}
    for fname in os.listdir(KNOWLEDGE_DIR):
        if fname.lower().endswith(".md"):
            key = os.path.splitext(fname)[0]
            with open(os.path.join(KNOWLEDGE_DIR, fname), "r", encoding="utf-8") as f:
                res[key] = f.read()
    return res
