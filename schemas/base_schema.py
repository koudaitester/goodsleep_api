# schemas/base_schema.py
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
