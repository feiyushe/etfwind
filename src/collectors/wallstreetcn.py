"""华尔街见闻 Playwright 采集器"""

import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from loguru import logger

from src.models import NewsItem, SourceType
from .playwright_base import PlaywrightCollector


class WallStreetCNCollector(PlaywrightCollector):
    """华尔街见闻快讯采集器"""

    def __init__(self):
        super().__init__(timeout=30000)
        self.wait_time = 5000  # 需要等待动态内容加载

    async def get_urls(self) -> list[str]:
        return ["https://wallstreetcn.com/live/global"]

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

        # 新版页面结构：查找所有 time 元素
        time_pattern = re.compile(r'^\d{1,2}:\d{2}$')

        for time_el in soup.find_all('time'):
            try:
                time_text = time_el.get_text(strip=True)
                # 只匹配 HH:MM 格式的时间（快讯时间）
                if not time_pattern.match(time_text):
                    continue

                # 获取父容器
                container = time_el.find_parent()
                if not container:
                    continue
                # 再往上一层获取整个快讯块
                news_block = container.find_parent()
                if not news_block:
                    continue

                # 获取所有段落文本
                paragraphs = news_block.find_all('p')
                if paragraphs:
                    texts = [p.get_text(strip=True) for p in paragraphs]
                    title = ' '.join(texts)
                else:
                    # 获取整个块的文本，移除时间部分
                    title = news_block.get_text(strip=True)
                    title = title.replace(time_text, '').strip()

                # 过滤太短或无效的内容
                if not title or len(title) < 10:
                    continue
                # 过滤导航和广告
                if any(k in title for k in ['登录', '注册', 'VIP', '下载', '查看更多']):
                    continue

                pub_time = self._parse_time(time_text, beijing_tz)

                items.append(NewsItem(
                    title=title[:500],  # 限制长度
                    content=title,
                    source="华尔街见闻",
                    source_type=SourceType.INTERNATIONAL,
                    url=url,
                    published_at=pub_time,
                ))
            except Exception as e:
                logger.debug(f"解析华尔街见闻条目失败: {e}")
                continue

        # 去重
        seen = set()
        unique_items = []
        for item in items:
            if item.title not in seen:
                seen.add(item.title)
                unique_items.append(item)

        return unique_items[:30]

    def _parse_time(self, time_text: str, tz) -> datetime:
        now = datetime.now(tz)
        match = re.search(r"(\d{1,2}):(\d{2})", time_text)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return now
