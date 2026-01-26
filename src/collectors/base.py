"""采集器基类"""

from abc import ABC, abstractmethod
from typing import Optional
import httpx
from loguru import logger

from src.models import NewsItem


class BaseCollector(ABC):
    """新闻采集器基类"""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        """采集器名称"""
        return self.__class__.__name__

    async def get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @abstractmethod
    async def collect(self) -> list[NewsItem]:
        """采集新闻，子类实现"""
        pass

    async def safe_collect(self) -> list[NewsItem]:
        """安全采集，捕获异常"""
        try:
            items = await self.collect()
            logger.info(f"{self.name} 采集到 {len(items)} 条新闻")
            return items
        except Exception as e:
            logger.error(f"{self.name} 采集失败: {e}")
            return []
