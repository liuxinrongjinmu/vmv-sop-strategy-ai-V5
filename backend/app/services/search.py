from typing import List, Dict
import httpx
from app.config import settings

class SearchService:
    """
    搜索服务
    使用Tavily API进行搜索
    """
    
    def __init__(self):
        self.tavily_api_key = settings.tavily_api_key
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
        
        Returns:
            格式化的搜索结果列表
        """
        if not self.tavily_api_key:
            print("[Search] Tavily API密钥未配置")
            return []
        
        return await self._search_tavily(query, num_results)
    
    async def _search_tavily(self, query: str, num_results: int) -> List[Dict]:
        """
        使用Tavily搜索
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    headers={
                        "Authorization": f"Bearer {self.tavily_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": query,
                        "max_results": num_results,
                        "include_answer": False,
                        "include_raw_content": False
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("url", ""),
                        "snippet": item.get("content", "")
                    })
                
                print(f"[Search] Tavily搜索成功，返回{len(results)}条结果")
                return results
        except Exception as e:
            print(f"[Search] Tavily搜索失败: {e}")
            return []

search_service = SearchService()
