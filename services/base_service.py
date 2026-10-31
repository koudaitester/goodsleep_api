# services/base_service.py
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
