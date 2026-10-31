from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 配置模型，用于从环境变量和.env文件加载配置
    model_config = SettingsConfigDict(
        env_file=".env",          # 指定环境变量配置文件
        extra="ignore",          # 忽略额外的环境变量
        env_file_encoding="utf-8" # 指定.env文件的编码格式
    )

    # 服务基础配置
    SERVICE_NAME: str = "GoodSleep Env Assess"  # 服务名称
    SERVICE_DEBUG: bool = True                 # 是否开启调试模式

    # Ollama相关配置，用于大模型服务
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"  # Ollama服务的基础URL
    MOONDREAM_MODEL: str = "moondream"               # 使用的模型名称

    # Prompt 文件路径，交给 prompt_loader 读取
    PROMPT_MOLD_VISION: str = "./prompts/mold_vision_v4.txt"
    PROMPT_SLEEP_VISION: str = "./prompts/sleep_vision_v1.txt"

    # 贝叶斯开关（预留，后面调算法用）
    USE_BN: bool = True

    # 日志、SSE调试面板开关
    ENABLE_SSE_LOG: bool = True

    # 睡眠CO2检测阈值
    SLEEP_CO2_THRESHOLD: int = 1000

settings = Settings()
