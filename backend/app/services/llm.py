from typing import Optional
import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)

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
        # 如果指定了provider则只尝试该provider，否则按主备顺序尝试
        if provider:
            providers = [provider]
        else:
            providers = [self.primary_provider, self.fallback_provider]
            # 过滤掉没有配置API key的provider
            providers = [p for p in providers if self._has_api_key(p)]
        
        logger.info(f"开始生成文本，使用提供商: {providers}")
        logger.debug(f"提示词长度: {len(prompt)} 字符")
        
        errors = []
        for p in providers:
            try:
                logger.info(f"调用模型: {p}")
                if p == "zhipu":
                    result = await self._call_zhipu(prompt, temperature, max_tokens)
                    logger.info(f"模型 {p} 调用成功，结果长度: {len(result)} 字符")
                    return result
                elif p == "qwen":
                    result = await self._call_qwen(prompt, temperature, max_tokens)
                    logger.info(f"模型 {p} 调用成功，结果长度: {len(result)} 字符")
                    return result
            except Exception as e:
                error_msg = f"模型 {p} 调用失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                # 如果还有备用provider，继续尝试
                continue
        
        raise Exception(f"所有模型调用失败: {'; '.join(errors)}")
    
    def _has_api_key(self, provider: str) -> bool:
        """检查provider是否配置了API key"""
        if provider == "zhipu":
            return bool(self.zhipu_api_key)
        elif provider == "qwen":
            return bool(self.qwen_api_key)
        return False
    
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
        使用OpenAI兼容格式（DashScope兼容模式）
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.qwen_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-max",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

llm_service = LLMService()
