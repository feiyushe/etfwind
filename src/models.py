"""数据模型"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"


class NewsCategory(str, Enum):
    MACRO = "macro"
    INDUSTRY = "industry"
    COMPANY = "company"
    INTERNATIONAL = "international"
    OTHER = "other"


class NewsItem(BaseModel):
    """新闻条目"""
    title: str
    content: str = ""
    source: str
    source_type: SourceType = SourceType.DOMESTIC
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    category: NewsCategory = NewsCategory.OTHER
    language: str = "zh"
    summary_zh: Optional[str] = None


class NewsCollection(BaseModel):
    """新闻集合"""
    items: list[NewsItem] = Field(default_factory=list)
    collected_at: datetime = Field(default_factory=datetime.now)

    @property
    def count(self) -> int:
        return len(self.items)
