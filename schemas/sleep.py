from pydantic import BaseModel, Field
from typing import Optional

class SleepVisionReq(BaseModel):
    image_b64: str = Field(..., description="图片base64")

class SleepVisionResp(BaseModel):
    raw_desc: str = Field(..., description="大模型原始卧室描述文本")

class SleepVisionObservation(BaseModel):
    air_hint: str
    mold_moisture: str
    vent_condition: str
    furniture_layout: str
    electronics: str
    bed_occlusion: str
    bedding_status: str
    mattress_situation: str
    clutter_level: str
    dust_accumulation: str
    window_curtain: str
    light_source: str
    wall_ceiling: str
    odor_cue: str
    space_type: str
    __raw_text__: str
    infer_cost_sec: Optional[float] = None  # 改成可选

    class Config:
        extra = "ignore"

class SleepEnvEvalReq(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2: Optional[float] = None
    noise: Optional[float] = None
    illuminance: Optional[float] = None
    sleep_start_hour: Optional[int] = None
    mold_risk_level: Optional[str] = None
    vision_obs: Optional[SleepVisionObservation] = None

# 配置类，用于定义配置项
    class Config:
    # 忽略额外的字段，只处理已定义的字段
        extra = "ignore"

class SleepEnvEvalResp(BaseModel):
    riskLevel: str
    riskClass: str
    desc: str
    suggest: str
    extraNote: str
    bayes: dict
