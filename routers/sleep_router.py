from fastapi import APIRouter, File, UploadFile, Form, logger
from schemas.sleep import SleepVisionReq, SleepVisionResp, SleepEnvEvalReq, SleepEnvEvalResp
from services.moondream_service import moondream_service
from services.sleep_env_service import SleepEnvService
import base64
from schemas.sleep import SleepVisionObservation
from services.log_service import logger
from services.base_service import BaseService
from services.sleep_env_service import sleep_env_service

router = APIRouter(prefix="/api/v1/sleep")

@router.post("/vision")
async def sleep_vision(
    img_file: UploadFile = File(...),  # 上传的文件参数，必填
    temperature: float = Form(..., description="环境温度"),  # 环境温度参数，必填，带描述
    humidity: float = Form(..., description="环境湿度")  # 环境湿度参数，必填，带描述
):
    # 读取图片二进制，转base64给MoonService
    img_bytes = await img_file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    result = await moondream_service.analyze_sleep_visual(img_b64)
    img_struct = result["data"]
    logger.info(f"img_struct: {img_struct}")
    vision_obs = SleepVisionObservation(**img_struct)
    raw_txt = result["data"]["__raw_text__"]
    pack = {
        **vision_obs.dict(),
        "temperature": temperature,
        "humidity": humidity
    }
    return {"code": 200, "msg": "ok", "data": pack}

@router.post("/eval", response_model=SleepEnvEvalResp)
async def sleep_eval(req: SleepEnvEvalReq):
    return await sleep_env_service.evaluate(req)

