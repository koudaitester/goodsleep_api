# config/prompt_loader.py
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
