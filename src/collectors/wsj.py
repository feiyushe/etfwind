"""WSJ 新闻采集器"""

from src.models import SourceType
from .rss_base import RSSCollector


class WSJCollector(RSSCollector):
    """Wall Street Journal RSS 采集器"""

    RSS_URL = "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
    SOURCE_NAME = "WSJ"
    SOURCE_TYPE = SourceType.INTERNATIONAL
    LANGUAGE = "en"
