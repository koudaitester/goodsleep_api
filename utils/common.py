# utils/common.py
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
