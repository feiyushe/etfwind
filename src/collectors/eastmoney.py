"""东方财富新闻采集器"""

import json
import re
from datetime import datetime
from typing import Any

from loguru import logger

from src.models import NewsItem, NewsCategory
from .base import BaseCollector


class EastMoneyCollector(BaseCollector):
    """东方财富财经要闻采集器"""

    API_URL = "https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html"

    async def collect(self) -> list[NewsItem]:
        """采集东方财富要闻"""
        client = await self.get_client()

        response = await client.get(self.API_URL)
        response.raise_for_status()

        # 解析 JSONP 格式: var ajaxResult={...}
        text = response.text
        match = re.search(r"var ajaxResult=(\{.*\})", text)
        if not match:
            logger.warning("东方财富 API 返回格式异常")
            return []

        data = json.loads(match.group(1))
        items = []

        news_list = data.get("LivesList", [])
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

            content = item.get("digest", "") or title
            url = item.get("url_w")

            # 解析时间
            show_time = item.get("showtime")
            published_at = None
            if show_time:
                try:
                    published_at = datetime.strptime(show_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass

            category = self._classify(title + content)

            return NewsItem(
                title=title,
                content=content,
                source="东方财富",
                url=url,
                published_at=published_at,
                category=category,
            )
        except Exception as e:
            logger.debug(f"解析东方财富新闻失败: {e}")
            return None

    def _classify(self, text: str) -> NewsCategory:
        """简单分类"""
        if any(k in text for k in ["央行", "政策", "国务院", "发改委", "财政", "货币"]):
            return NewsCategory.MACRO
        if any(k in text for k in ["美股", "美联储", "欧洲", "日本", "外资", "港股"]):
            return NewsCategory.INTERNATIONAL
        if any(k in text for k in ["板块", "行业", "概念", "赛道", "产业链"]):
            return NewsCategory.INDUSTRY
        if any(k in text for k in ["公司", "股份", "集团", "业绩", "财报", "增持"]):
            return NewsCategory.COMPANY
        return NewsCategory.OTHER
