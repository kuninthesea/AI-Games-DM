from openai import OpenAI
import google.generativeai as genai
import concurrent.futures
from config import OPENAI_API_KEY, OPENAI_BASE_URL, GEMINI_API_KEY, DEFAULT_MODEL

# 创建 OpenAI 客户端
client = OpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY
)

def call_ai_api(model_choice, messages):
    """调用AI API的统一方法"""
    if model_choice == "gemini":
        # Gemini API 调用
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            
            # 构建提示词
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            
            # 尝试不同的模型名称
            model_names = ['gemini-1.5-pro', 'gemini-pro', 'gemini-1.5-flash']
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(model.generate_content, prompt)
                        try:
                            response = future.result(timeout=15)
                            return response.text.strip()
                        except concurrent.futures.TimeoutError:
                            continue
                except Exception:
                    continue
            
            return "所有Gemini模型都无法访问，请检查API Key或网络连接"
                    
        except Exception as e:
            return f"Gemini API配置失败: {e}"
    else:
        # 使用默认模型通过 xiaoai.plus
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages
            )
            reply = response.choices[0].message.content
            return reply
        except Exception as e:
            return f"API错误: {str(e)}"
