"""金十数据 Playwright 采集器"""

import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from loguru import logger

from src.models import NewsItem, SourceType
from .playwright_base import PlaywrightCollector


class Jin10Collector(PlaywrightCollector):
    """金十数据快讯采集器"""

    def __init__(self):
        super().__init__(timeout=30000)
        self.wait_time = 5000  # 金十需要更长等待时间

    async def get_urls(self) -> list[str]:
        return ["https://www.jin10.com/"]

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

        # 新版金十数据页面结构：查找包含时间和内容的快讯块
        # 时间格式如 14:25:13，内容在相邻元素
        all_text = soup.get_text()

        # 查找所有时间戳和对应内容
        time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2})')

        # 遍历所有包含时间的元素
        for el in soup.find_all(string=time_pattern):
            try:
                parent = el.find_parent()
                if not parent:
                    continue

                # 获取时间
                time_match = time_pattern.search(el)
                if not time_match:
                    continue
                time_text = time_match.group(1)

                # 查找相邻的内容元素
                container = parent.find_parent()
                if not container:
                    continue

                # 获取容器内所有文本
                full_text = container.get_text(strip=True)
                # 移除时间部分
                title = full_text.replace(time_text, '').strip()

                # 清理常见的无关前缀
                noise_prefixes = ['分享收藏详情复制', '分享收藏', '详情复制', '复制']
                for prefix in noise_prefixes:
                    if title.startswith(prefix):
                        title = title[len(prefix):].strip()

                # 过滤太短或无效的内容
                if not title or len(title) < 15:
                    continue
                # 过滤导航和广告
                if any(k in title for k in ['登录', '更多', '查看', 'VIP', '解锁', '订阅', '金十期货']):
                    continue

                pub_time = self._parse_time(time_text, beijing_tz)

                items.append(NewsItem(
                    title=title[:200],  # 限制长度
                    content=title,
                    source="金十数据",
                    source_type=SourceType.INTERNATIONAL,
                    url=url,
                    published_at=pub_time,
                ))
            except Exception as e:
                logger.debug(f"解析金十条目失败: {e}")
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
        match = re.search(r"(\d{1,2}):(\d{2}):(\d{2})", time_text)
        if match:
            h, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return now.replace(hour=h, minute=m, second=s, microsecond=0)
        return now
