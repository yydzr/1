"""
DeepSeek AI 客户端（兼容 OpenAI SDK）
支持系统默认 Key 和用户自定义 Key
"""
from openai import OpenAI
from config import Config


def _make_client(api_key=None):
    """创建 AI 客户端，优先使用传入的 api_key"""
    key = api_key or Config.DEEPSEEK_API_KEY
    # 检查 Key 是否为占位符（无效）
    if not key or key.startswith('sk-your-') or key == 'your-api-key':
        raise ValueError('AI_API_KEY_NOT_SET')
    return OpenAI(api_key=key, base_url=Config.DEEPSEEK_BASE_URL)


def chat(user_prompt, system_prompt=None, temperature=0.7, max_tokens=2000, api_key=None):
    """
    单轮对话，返回 AI 回复文本

    参数:
        user_prompt: 用户输入
        system_prompt: 系统角色提示（可选）
        temperature: 创造性程度 0-1
        max_tokens: 最大返回长度
        api_key: 用户自定义 API Key（可选）

    返回:
        str: AI 回复内容
    """
    client = _make_client(api_key)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=Config.DEEPSEEK_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def chat_json(user_prompt, system_prompt=None, temperature=0.3, api_key=None):
    """
    对话并期望返回 JSON 格式（用于结构化提取）
    返回解析后的 dict，失败返回 None
    """
    import json
    full_system = (system_prompt or "") + "\n请只返回合法的 JSON 格式，不要包含其他文字。"
    text = chat(user_prompt, full_system, temperature=temperature, api_key=api_key)
    try:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines)
        return json.loads(text)
    except (json.JSONDecodeError, Exception):
        return None
