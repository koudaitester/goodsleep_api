from pydantic import BaseModel, Field
from typing import Optional

class SleepVisionReq(BaseModel):
    image_b64: str = Field(..., description="图片base64")

class SleepVisionResp(BaseModel):
    raw_desc: str = Field(..., description="大模型原始卧室描述文本")

class SleepEnvEvalReq(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2: Optional[int] = None
    noise: Optional[float] = None
    illuminance: Optional[float] = None
    time_period: str = Field(..., description="时段：bedtime / midnight / dawn")
    mold_risk_level: Optional[str] = None # 复用霉菌模块输出：低/初级/中/高

class SleepEnvEvalResp(BaseModel):
    riskLevel: str
    riskClass: str
    desc: str
    suggest: str
    extraNote: str
    bayes: dict
