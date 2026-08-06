"""
DeepSeek API 调用封装（OpenAI 兼容接口）
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"


def get_client() -> OpenAI:
    """获取 DeepSeek 客户端实例"""
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> str:
    """
    调用 DeepSeek API 生成内容

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        temperature: 温度参数（0-1，越高越随机）
        max_tokens: 最大输出 token 数

    Returns:
        AI 生成的文本内容

    Raises:
        ValueError: API Key 未配置
        Exception: API 调用失败
    """
    api_key = DEEPSEEK_API_KEY
    if not api_key or api_key == "sk-your-deepseek-api-key-here":
        raise ValueError(
            "DeepSeek API Key 未配置！\n"
            "请在 demo/.env 文件中设置 DEEPSEEK_API_KEY=你的真实Key"
        )

    client = get_client()

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content or ""

    except Exception as e:
        raise Exception(f"DeepSeek API 调用失败: {str(e)}")


def check_api_available() -> dict:
    """
    检查 API Key 是否已配置

    Returns:
        {"available": bool, "message": str}
    """
    api_key = DEEPSEEK_API_KEY
    if not api_key or api_key == "sk-your-deepseek-api-key-here":
        return {
            "available": False,
            "message": "DeepSeek API Key 未配置。请在 demo/.env 文件中设置 DEEPSEEK_API_KEY"
        }
    return {
        "available": True,
        "message": f"API Key 已配置 (模型: {DEEPSEEK_MODEL})"
    }
