"""Bloomberg 新闻采集器"""

from src.models import SourceType
from .rss_base import RSSCollector


class BloombergCollector(RSSCollector):
    """Bloomberg RSS 采集器"""

    RSS_URL = "https://feeds.bloomberg.com/markets/news.rss"
    SOURCE_NAME = "Bloomberg"
    SOURCE_TYPE = SourceType.INTERNATIONAL
    LANGUAGE = "en"
