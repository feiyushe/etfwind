"""证券时报新闻采集器"""

import re
from datetime import datetime, date

from bs4 import BeautifulSoup
from loguru import logger

from src.models import NewsItem, NewsCategory
from .base import BaseCollector


class StcnCollector(BaseCollector):
    """证券时报滚动新闻采集器

    抓取 stcn.com 滚动新闻页（服务端渲染 HTML），
    用 BeautifulSoup 解析标题、链接、时间。
    """

    PAGE_URL = "https://www.stcn.com/article/list/gd.html"
    BASE_URL = "https://www.stcn.com"

    async def collect(self) -> list[NewsItem]:
        """采集证券时报滚动新闻"""
        client = await self.get_client()

        response = await client.get(self.PAGE_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        items: list[NewsItem] = []

        # 遍历每个 <li>，从 div.tt 中提取标题链接（避免匹配摘要和缩略图的重复链接）
        for li in soup.select("ul.list > li"):
            news = self._parse_li(li)
            if news:
                items.append(news)

        return items

    def _parse_li(self, li) -> NewsItem | None:
        """解析单个 <li> 新闻条目

        页面结构：
          <li>
            <div class="content">
              <div class="tt"><a href="/article/detail/ID.html">标题</a></div>
              <div class="text ellipsis-2"><a>摘要...</a></div>
              <div class="info"><span>栏目</span><span>作者</span><span>HH:MM</span></div>
            </div>
          </li>
        """
        try:
            # 从 div.tt 提取标题和链接
            tt_div = li.select_one("div.tt")
            if not tt_div:
                return None
            a_tag = tt_div.find("a", href=re.compile(r"/article/detail/\d+\.html"))
            if not a_tag:
                return None

            title = a_tag.get_text(strip=True)
            if not title or len(title) < 4:
                return None

            # 构建完整 URL
            href = a_tag.get("href", "")
            url = href if href.startswith("http") else self.BASE_URL + href

            # 从 div.text 提取摘要作为 content
            text_div = li.select_one("div.text")
            content = text_div.get_text(strip=True) if text_div else title

            # 从 div.info 最后一个 <span> 提取时间
            published_at = self._extract_time(li)

            category = self._classify(title)

            return NewsItem(
                title=title,
                content=content,
                source="证券时报",
                url=url,
                published_at=published_at,
                category=category,
            )
        except Exception as e:
            logger.debug(f"解析证券时报新闻失败: {e}")
            return None

    def _extract_time(self, li) -> datetime | None:
        """从 div.info 的最后一个 <span> 提取发布时间（HH:MM 格式）"""
        info_div = li.select_one("div.info")
        if not info_div:
            return None

        spans = info_div.find_all("span")
        if not spans:
            return None

        # 时间通常在最后一个 span
        for span in reversed(spans):
            text = span.get_text(strip=True)
            match = re.search(r"(\d{1,2}):(\d{2})", text)
            if match:
                hour, minute = int(match.group(1)), int(match.group(2))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    today = date.today()
                    return datetime(today.year, today.month, today.day, hour, minute)
        return None

    def _classify(self, text: str) -> NewsCategory:
        """简单分类"""
        if any(k in text for k in ["央行", "政策", "国务院", "发改委", "财政", "证监会"]):
            return NewsCategory.MACRO
        if any(k in text for k in ["美股", "美联储", "欧洲", "日本", "外资"]):
            return NewsCategory.INTERNATIONAL
        if any(k in text for k in ["板块", "行业", "概念", "赛道", "ETF"]):
            return NewsCategory.INDUSTRY
        if any(k in text for k in ["公司", "股份", "集团", "业绩", "财报"]):
            return NewsCategory.COMPANY
        return NewsCategory.OTHER
