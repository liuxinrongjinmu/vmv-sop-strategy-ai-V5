from typing import Optional
import httpx
from app.config import settings
import traceback

class LLMService:
    """
    大模型服务
    封装智谱和千问API调用，支持主备切换
    """
    
    def __init__(self):
        self.zhipu_api_key = settings.zhipu_api_key
        self.qwen_api_key = settings.qwen_api_key
        self.primary_provider = settings.llm_primary_provider
        self.fallback_provider = settings.llm_fallback_provider
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        provider: Optional[str] = None
    ) -> str:
        """
        生成文本响应
        自动处理主备切换
        
        Args:
            prompt: 输入提示
            temperature: 温度参数
            max_tokens: 最大token数
            provider: 指定提供商
        
        Returns:
            生成的文本
        """
        providers = [provider] if provider else [self.primary_provider]  # 只尝试主提供商
        
        print(f"[LLM] 开始生成文本，使用提供商: {providers}")
        print(f"[LLM] 提示词长度: {len(prompt)} 字符")
        
        errors = []
        for p in providers:
            try:
                print(f"[LLM] 调用模型: {p}")
                if p == "zhipu":
                    result = await self._call_zhipu(prompt, temperature, max_tokens)
                    print(f"[LLM] 模型 {p} 调用成功，结果长度: {len(result)} 字符")
                    return result
                elif p == "qwen":
                    result = await self._call_qwen(prompt, temperature, max_tokens)
                    print(f"[LLM] 模型 {p} 调用成功，结果长度: {len(result)} 字符")
                    return result
            except Exception as e:
                error_msg = f"模型 {p} 调用失败: {str(e)}"
                print(f"[LLM] {error_msg}")
                print(f"[LLM] 错误详情: {traceback.format_exc()}")
                errors.append(error_msg)
                continue
        
        raise Exception(f"模型调用失败: {'; '.join(errors)}")
    
    async def _call_zhipu(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """
        调用智谱GLM-4 API
        """
        async with httpx.AsyncClient(timeout=60.0) as client:  # 减少超时到60秒
            response = await client.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.zhipu_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_qwen(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """
        调用千问Max API
        """
        async with httpx.AsyncClient(timeout=60.0) as client:  # 减少超时到60秒
            response = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.qwen_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-max",
                    "input": {"prompt": prompt},
                    "parameters": {
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["output"]["text"]

llm_service = LLMService()
