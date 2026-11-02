# main.py
from asyncio import sleep

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from routers import sleep_router
from services.log_service import logger
from routers.logview_router import router as logview_router
from routers.sleep_router import router as sleep_router
from typing import Any
from services.base_service import BaseResp


os.makedirs("./tmp", exist_ok=True)

app = FastAPI(title="goodsleep_api", version="0.1.0")

app.mount("/html_basic/static", StaticFiles(directory="html_basic/static"), name="static")
app.include_router(logview_router, prefix="")
app.include_router(sleep_router, prefix="")


@app.get("/", tags=["首页"])
async def root():
    logger.info("访问根路径")
    return RedirectResponse(url="/html_basic/static/index.html")


if __name__ == "__main__":
    import uvicorn
    logger.info("服务启动")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
