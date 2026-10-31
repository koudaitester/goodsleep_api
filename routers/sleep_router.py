from fastapi import APIRouter, File, UploadFile
from schemas.sleep import SleepVisionReq, SleepVisionResp, SleepEnvEvalReq, SleepEnvEvalResp
from services.moondream_service import moondream_service
from services.sleep_env_service import SleepEnvService


router = APIRouter()

@router.post("/vision")
async def sleep_vision(file: UploadFile = File(...)):
    # 读取图片二进制，转base64给MoonService
    import base64
    img_bytes = await file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    result = await moondream_service.analyze_mold_visual(img_b64)
    return result

@router.post("/eval", response_model=SleepEnvEvalResp)
async def sleep_eval(req: SleepEnvEvalReq):
    return SleepEnvService.evaluate(req)
