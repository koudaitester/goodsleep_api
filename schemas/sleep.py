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
    infer_cost_sec: float
    raw_text: str = Field(..., alias="__raw_text__")
    
    class Config:
        extra = "ignore"

class SleepEnvEvalReq(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2: Optional[int] = None
    noise: Optional[float] = None
    illuminance: Optional[float] = None
    time_period: str = Field(..., description="时段：bedtime / midnight / dawn")
    mold_risk_level: Optional[str] = None # 复用霉菌模块输出：低/初级/中/高
    # 新增：视觉观测证据包，可选，类型就是上面的SleepVisionObservation
    vision_obs: Optional[SleepVisionObservation] = None

    class Config:
        extra = "ignore"

class SleepEnvEvalResp(BaseModel):
    riskLevel: str
    riskClass: str
    desc: str
    suggest: str
    extraNote: str
    bayes: dict
