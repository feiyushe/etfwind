"""CNBC 新闻采集器"""

from src.models import SourceType
from .rss_base import RSSCollector


class CNBCCollector(RSSCollector):
    """CNBC RSS 采集器"""

    RSS_URL = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147"
    SOURCE_NAME = "CNBC"
    SOURCE_TYPE = SourceType.INTERNATIONAL
    LANGUAGE = "en"
