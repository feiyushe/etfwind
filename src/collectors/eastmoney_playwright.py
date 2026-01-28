"""东方财富快讯 Playwright 采集器"""

import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from loguru import logger

from src.models import NewsItem, SourceType
from .playwright_base import PlaywrightCollector


class EastMoneyPlaywrightCollector(PlaywrightCollector):
    """东方财富快讯采集器（Playwright 版本）"""

    def __init__(self):
        super().__init__(timeout=30000)
        self.wait_time = 3000  # 等待动态内容加载

    async def get_urls(self) -> list[str]:
        return ["https://kuaixun.eastmoney.com/"]

    async def fetch_page(self, url: str):
        """重写 fetch_page 增加等待时间"""
        try:
            from .playwright_base import get_browser
            browser = await get_browser()
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                await page.wait_for_timeout(self.wait_time)
                content = await page.content()
                return content
            finally:
                await page.close()
        except Exception as e:
            logger.warning(f"{self.name} 获取页面失败 {url}: {e}")
            return None

    async def parse_page(self, url: str, content: str) -> list[NewsItem]:
        soup = BeautifulSoup(content, "html.parser")
        items = []
        beijing_tz = timezone(timedelta(hours=8))

        # 新版页面结构：查找所有包含 finance.eastmoney.com 链接的 a 标签
        for link in soup.find_all('a', href=True):
            try:
                href = link.get('href', '')
                # 只处理财经新闻链接
                if 'finance.eastmoney.com' not in href:
                    continue

                # 获取链接文本
                title = link.get_text(strip=True)
                # 移除 [点击查看全文] 后缀
                title = re.sub(r'\[点击查看全文\]$', '', title).strip()

                if not title or len(title) < 10:
                    continue

                # 过滤广告和无效内容
                if any(k in title for k in ['登录', '注册', 'VIP', '下载', '更多']):
                    continue

                news_url = href
                if news_url.startswith("//"):
                    news_url = "https:" + news_url

                items.append(NewsItem(
                    title=title[:500],
                    content=title,
                    source="东财快讯",
                    source_type=SourceType.DOMESTIC,
                    url=news_url,
                    published_at=datetime.now(beijing_tz),
                ))
            except Exception as e:
                logger.debug(f"解析东财条目失败: {e}")
                continue

        # 去重
        seen = set()
        unique_items = []
        for item in items:
            if item.title not in seen:
                seen.add(item.title)
                unique_items.append(item)

        return unique_items[:30]
