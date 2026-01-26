"""新浪财经新闻采集器"""

from datetime import datetime
from typing import Any

from loguru import logger

from src.models import NewsItem, NewsCategory
from .base import BaseCollector


class SinaFinanceCollector(BaseCollector):
    """新浪财经新闻采集器"""

    API_URL = "https://feed.mix.sina.com.cn/api/roll/get"

    async def collect(self) -> list[NewsItem]:
        """采集新浪财经新闻"""
        client = await self.get_client()

        params = {
            "pageid": "153",
            "lid": "2516",
            "k": "",
            "num": 50,
            "page": 1,
        }

        response = await client.get(self.API_URL, params=params)
        response.raise_for_status()

        data = response.json()
        items = []

        news_list = data.get("result", {}).get("data", [])
        for item in news_list:
            news = self._parse_item(item)
            if news:
                items.append(news)

        return items

    def _parse_item(self, item: dict[str, Any]) -> NewsItem | None:
        """解析单条新闻"""
        try:
            title = item.get("title", "")
            if not title:
                return None

            content = item.get("intro", "") or title
            url = item.get("url")

            # 解析时间
            ctime = item.get("ctime")
            published_at = None
            if ctime:
                try:
                    published_at = datetime.fromtimestamp(int(ctime))
                except (ValueError, TypeError):
                    pass

            category = self._classify(title + content)

            return NewsItem(
                title=title,
                content=content,
                source="新浪财经",
                url=url,
                published_at=published_at,
                category=category,
            )
        except Exception as e:
            logger.debug(f"解析新浪财经新闻失败: {e}")
            return None

    def _classify(self, text: str) -> NewsCategory:
        """简单分类"""
        if any(k in text for k in ["央行", "政策", "国务院", "发改委", "财政"]):
            return NewsCategory.MACRO
        if any(k in text for k in ["美股", "美联储", "欧洲", "日本", "外资"]):
            return NewsCategory.INTERNATIONAL
        if any(k in text for k in ["板块", "行业", "概念", "赛道"]):
            return NewsCategory.INDUSTRY
        if any(k in text for k in ["公司", "股份", "集团", "业绩"]):
            return NewsCategory.COMPANY
        return NewsCategory.OTHER
