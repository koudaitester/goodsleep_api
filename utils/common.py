# utils/common.py
import re
import json
import io
import base64


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

# utils/common.py
def bayes_two_pair(
    prior_h: float,
    p_x_given_h: dict,
    p_x_given_not_h: dict,
    p_y_given_h_x: dict,
    p_y_given_not_h_x: dict,
    x_state: str,
    y_state: str,
    scale: float
) -> tuple[float, float]:
    ph = prior_h
    pnh = 1.0 - ph

    p_x_h = p_x_given_h[x_state]
    p_y_hx = p_y_given_h_x[(x_state, y_state)]

    p_x_nh = p_x_given_not_h[x_state]
    p_y_nhx = p_y_given_not_h_x[(x_state, y_state)]

    joint_h = ph * p_x_h * p_y_hx
    joint_nh = pnh * p_x_nh * p_y_nhx
    denom = joint_h + joint_nh
    if denom <= 0:
        return 0.0, 0.0
    post = joint_h / denom
    add_delta = post * scale
    return post, add_delta
