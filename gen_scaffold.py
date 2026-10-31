# gen_scaffold.py
"""
极简FastAPI脚手架生成器
--name 项目名
--ext 生成扩展模块
"""
import os
import argparse

def render_text(tpl: str, project_name: str) -> str:
    return tpl.replace("Env POC Scaffold", project_name)

core_tpl = {
    "config/prompt_config.py": '''# config/prompt_config.py
from typing import Dict

PROMPT_TEMPLATES: Dict[str, str] = {
    "moondream_visual": """你是室内人居环境检测助手，识别图片里的霉斑、水渍、返潮痕迹。
区分：霉斑 / 水渍 / 普通污渍，不要幻觉。
输出结构化结论。"""
}
''',
    "config/prompt_loader.py": '''# config/prompt_loader.py
from config.prompt_config import PROMPT_TEMPLATES


class PromptNotFoundError(Exception):
    """模板不存在异常"""
    pass


def get_raw_prompt_template(template_key: str) -> str:
    """获取原始prompt模板文本，不做渲染"""
    if template_key not in PROMPT_TEMPLATES:
        raise PromptNotFoundError(
            f"Prompt模板[{template_key}]不存在，可用模板：{list(PROMPT_TEMPLATES.keys())}"
        )
    return PROMPT_TEMPLATES[template_key]


def get_prompt(template_key: str, **kwargs) -> str:
    """
    获取并渲染prompt模板
    :param template_key: 模板key名称
    :param kwargs: 占位符变量，用于str.format填充
    :return: 渲染完成的prompt字符串
    """
    template = get_raw_prompt_template(template_key)
    try:
        rendered = template.format(**kwargs)
    except KeyError:
        rendered = template
    return rendered


__all__ = ["get_prompt"]
''',
    "schemas/base_schema.py": '''# schemas/base_schema.py
from typing import Any
from pydantic import BaseModel


class BaseResp(BaseModel):
    code: int
    msg: str
    data: Any = None

    @staticmethod
    def ok(data: Any = None, msg: str = "ok") -> "BaseResp":
        return BaseResp(code=0, msg=msg, data=data)

    @staticmethod
    def fail(code: int = 400, msg: str = "fail", data: Any = None) -> "BaseResp":
        return BaseResp(code=code, msg=msg, data=data)
''',
    "services/base_service.py": '''# services/base_service.py
from typing import Any
from schemas.base_schema import BaseResp


class BaseService:
    """所有Service基类，统一返回封装"""
    @staticmethod
    def success(data: Any = None, msg: str = "ok") -> BaseResp:
        return BaseResp.ok(data=data, msg=msg)

    @staticmethod
    def fail(msg: str, code: int = 400, data: Any = None) -> BaseResp:
        return BaseResp.fail(code=code, msg=msg, data=data)
''',
    "services/log_service.py": '''# services/log_service.py
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from utils.sse_log_helper import push_log

LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)


class SseLogHandler(logging.Handler):
    """自定义日志Handler，日志消息自动推送到SSE缓冲区"""
    def emit(self, record):
        try:
            line = self.format(record)
            push_log(line)
        except Exception:
            pass


logger = logging.getLogger("Env POC Scaffold")
logger.setLevel(logging.INFO)
logger.propagate = False

log_format = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(log_format)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)

sse_handler = SseLogHandler()
sse_handler.setFormatter(log_format)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.addHandler(sse_handler)
''',
    "utils/sse_log_helper.py": '''# utils/sse_log_helper.py
import asyncio
from collections import deque

log_buffer = deque(maxlen=200)


def push_log(line: str):
    log_buffer.append(line)


async def log_stream_generator():
    while True:
        if log_buffer:
            line = log_buffer.popleft()
            yield f"data: {line}\\n\\n"
        await asyncio.sleep(0.15)
''',
    "utils/common.py": '''# utils/common.py
import re
import json
import io
import base64
from PIL import Image


def parse_json_safely(raw: str):
    """剥离markdown ```json 标记，安全解析json"""
    raw = re.sub(r"```(json)?", "", raw).strip()
    return json.loads(raw)


def resize_image_for_llava(img_b64: str, target_size: int = 672) -> str:
    """
    base64图片等比例缩放，长边限制为target_size
    返回压缩后的JPEG base64字符串
    """
    img_data = base64.b64decode(img_b64)
    img = Image.open(io.BytesIO(img_data)).convert("RGB")

    w, h = img.size
    if max(w, h) > target_size:
        scale = target_size / max(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
''',
    "utils/validator.py": '''# utils/validator.py
from typing import Any
import re


def validate_no_special_char(v: str) -> str:
    """防危险特殊字符过滤，用于文本输入，禁止 ; $ " ' < > { }"""
    if re.search(r"[;$\"'<>{}]", v):
        raise ValueError("内容包含非法特殊字符")
    return v.strip()


def validate_positive_number(v: float | int) -> float | int:
    """校验数值必须大于0，温湿度、图片尺寸等场景"""
    if v <= 0:
        raise ValueError("数值必须大于0")
    return v


def validate_range(v: float, min_val: float, max_val: float) -> float:
    """通用范围校验：校验数字落在 [min_val, max_val]"""
    if not (min_val <= v <= max_val):
        raise ValueError(f"数值必须在 {min_val} ~ {max_val} 之间")
    return v


class CommonValidators:
    """Pydantic 可复用校验器类，直接 @field_validator 调用"""
    @classmethod
    def str_strip(cls, v: Any) -> Any:
        """字符串自动去除首尾空白，非字符串原样返回"""
        if isinstance(v, str):
            return v.strip()
        return v
''',
    "utils/knowledge_loader.py": '''# utils/knowledge_loader.py
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
''',
    "routers/logview_router.py": '''# routers/logview_router.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from utils.sse_log_helper import log_stream_generator

router = APIRouter()


@router.get("/stream")
async def log_stream():
    """SSE实时日志流"""
    return StreamingResponse(log_stream_generator(), media_type="text/event-stream")
''',
    "html_basic/static/index.html": '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>人居微环境视觉检测系统</title>
<style>
* {
margin: 0;
padding: 0;
box-sizing: border-box;
font-family: system-ui, sans-serif;
}
body {
height: 100vh;
overflow: hidden;
}
.container {
display: flex;
height: 100%;
}
.sidebar {
width: 220px;
background-color: #2c3e50;
color: #fff;
padding-top: 24px;
transition: 0.3s;
}
.sidebar .menu-item {
padding: 14px 24px;
cursor: pointer;
font-size: 16px;
}
.sidebar .menu-item:hover {
background-color: #34495e;
}
.sidebar .menu-item.active {
background-color: #3498db;
}
.main-content {
flex: 1;
height: 100%;
}
#content-iframe {
width: 100%;
height: 100%;
border: none;
}
.hamburger {
display: none;
position: fixed;
top: 12px;
left: 12px;
z-index: 99;
background: #2c3e50;
color: white;
border: none;
padding: 8px 12px;
font-size: 18px;
}
@media (max-width:768px){
.hamburger {
display: block;
}
.sidebar {
position: fixed;
left: -220px;
height: 100%;
z-index: 98;
}
.sidebar.open {
left: 0;
}
}
</style>
</head>
<body>
<button class="hamburger" id="hamburger">☰</button>
<div class="container">
<aside class="sidebar" id="sidebar">
<div class="menu-item active" data-src="mold_analyze.html">图片检测</div>
<div class="menu-item" data-src="mold_detect.html">视频轮巡检测</div>
<div class="menu-item" data-src="placeholder_help.html">使用帮助</div>
</aside>
<main class="main-content">
<iframe id="content-iframe" src="mold_analyze.html"></iframe>
</main>
</div>
<script>
const menuItems = document.querySelectorAll('.menu-item');
const iframe = document.getElementById('content-iframe');
const hamburger = document.getElementById('hamburger');
const sidebar = document.getElementById('sidebar');
menuItems.forEach(item => {
item.addEventListener('click', ()=>{
menuItems.forEach(mi=>mi.classList.remove('active'));
item.classList.add('active');
const pageUrl = item.getAttribute('data-src');
iframe.src = pageUrl;
if(window.innerWidth <=768){
sidebar.classList.remove('open');
}
})
})
hamburger.addEventListener('click',()=>{
sidebar.classList.toggle('open');
})
</script>
</body>
</html>''',
    "main.py": '''# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from services.log_service import logger
from routers.logview_router import router as logview_router


os.makedirs("./tmp", exist_ok=True)

app = FastAPI(title="Env POC Scaffold", version="0.1.0")

app.mount("/html_basic/static", StaticFiles(directory="html_basic/static"), name="static")
app.include_router(logview_router, prefix="/logview")


@app.get("/", tags=["首页"])
async def root():
    logger.info("访问根路径")
    return RedirectResponse(url="/html_basic/static/index.html")


if __name__ == "__main__":
    import uvicorn
    logger.info("服务启动")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
''',
    "requirements.txt": '''# requirements.txt
# ========== 核心必选 ==========
fastapi
uvicorn[standard]
pydantic>=2.0
python-multipart

# ========== 可选扩展（llm/图像） ==========
# ollama
# Pillow>=10.0
''',
    "README.md": ""
}

ext_tpl = {
    "services/llm_base_service.py": '''# services/llm_base_service.py
import ollama
from typing import Optional
from config.app_config import cfg
from services.base_service import BaseService
from services.log_service import logger


class LlmBaseService(BaseService):
    @staticmethod
    async def chat(
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        model_name = model or cfg.ollama.model_name
        temp = temperature if temperature is not None else cfg.ollama.temperature
        maxtok = max_tokens if max_tokens is not None else cfg.ollama.max_tokens
        ollama.base_url = cfg.ollama.base_url

        try:
            resp = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": temp,
                    "num_predict": maxtok
                }
            )
            return LlmBaseService.success(data=resp)
        except Exception as e:
            logger.exception("ollama chat failed")
            return LlmBaseService.fail(msg=f"大模型调用失败：{str(e)}")

    @staticmethod
    async def vision(
        prompt: str,
        image_bytes: bytes,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        model_name = model or cfg.ollama.model_name
        temp = temperature if temperature is not None else cfg.ollama.temperature
        maxtok = max_tokens if max_tokens is not None else cfg.ollama.max_tokens
        ollama.base_url = cfg.ollama.base_url

        try:
            resp = ollama.chat(
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [image_bytes]
                }],
                options={
                    "temperature": temp,
                    "num_predict": maxtok
                }
            )
            return LlmBaseService.success(data=resp)
        except Exception as e:
            logger.exception("ollama vision failed")
            return LlmBaseService.fail(msg=f"视觉模型调用失败：{str(e)}")
''',
    "services/user_service.py": '''# services/user_service.py
from services.dao.app_user_dao import (
    get_user_by_username as dao_get_user_by_username,
    create_user as dao_create_user
)
from utils.security import get_password_hash, verify_password
from typing import Optional, Dict


def get_user_by_username(username: str):
    return dao_get_user_by_username(username)


def create_user(username: str, password: str, nickname: str = None):
    hashed_pw = get_password_hash(password)
    return dao_create_user(username, hashed_pw, nickname)


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user
''',
    "utils/security.py": '''# utils/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
''',
    "schemas/env_schema.py": '''# schemas/env_schema.py
from pydantic import BaseModel
from utils.validator import validate_range


class EnvInput(BaseModel):
    temp: float
    humidity: float

    @classmethod
    @validate_range("temp", 0, 50)
    def check_temp(cls, v):
        return v

    @classmethod
    @validate_range("humidity", 0, 100)
    def check_hum(cls, v):
        return v
'''
}


def write_file(filepath: str, content: str):
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ {filepath}")


def main():
    parser = argparse.ArgumentParser(description="FastAPI脚手架生成器｜支持自定义项目名")
    parser.add_argument("--name", default="Env POC Scaffold", help="项目名称")
    parser.add_argument("--ext", action="store_true", help="同时生成可选扩展文件")
    args = parser.parse_args()
    proj_name = args.name

    print(f"=== 开始生成脚手架【{proj_name}】 ===")
    for fp, txt in core_tpl.items():
        write_file(fp, render_text(txt, proj_name))

    if args.ext:
        print("\n=== 开始生成扩展文件 ===")
        for fp, txt in ext_tpl.items():
            write_file(fp, render_text(txt, proj_name))

    for d in ("knowledge", "log", "tmp"):
        os.makedirs(d, exist_ok=True)
    print("\n🎉 脚手架生成完成！")


if __name__ == "__main__":
    main()

