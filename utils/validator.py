# utils/validator.py
from typing import Any
import re


def validate_no_special_char(v: str) -> str:
    """防危险特殊字符过滤，用于文本输入，禁止 ; $ " ' < > { }"""
    if re.search(r"[;$"'<>{}]", v):
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
