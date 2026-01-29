"""模拟测试模块 - 用假数据测试完整流程"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from loguru import logger


# 模拟新闻数据
MOCK_NEWS = [
    {"source": "财联社", "title": "黄金价格突破2800美元创历史新高，避险情绪升温"},
    {"source": "东方财富", "title": "芯片板块集体拉升，中芯国际涨超5%"},
    {"source": "华尔街见闻", "title": "特斯拉Q4交付量超预期，新能源车板块走强"},
    {"source": "金十数据", "title": "美联储释放鸽派信号，降息预期升温"},
    {"source": "财联社", "title": "光伏组件价格企稳，行业拐点或将到来"},
    {"source": "东方财富", "title": "证券板块异动，多只券商股涨停"},
    {"source": "华尔街见闻", "title": "锂电池龙头宁德时代发布新一代电池技术"},
    {"source": "金十数据", "title": "人工智能概念持续火热，算力需求激增"},
]

# 模拟 AI 分析结果
MOCK_ANALYSIS_RESULT = {
    "key_events": [
        "黄金价格突破2800美元创历史新高",
        "中芯国际涨超5%领涨芯片板块",
        "特斯拉Q4交付量超预期",
        "多只券商股涨停"
    ],
    "market_view": "🎯 避险升温+科技回暖，结构性行情延续",
    "narrative": "黄金突破历史新高反映全球避险情绪升温，美联储鸽派信号提振风险资产。科技板块分化，芯片受益国产替代逻辑，新能源车产业链在特斯拉带动下回暖。证券板块异动或预示市场情绪转暖，关注后续成交量配合。",
    "sectors": [
        {
            "name": "黄金",
            "heat": 5,
            "direction": "利好",
            "analysis": "金价突破2800美元创历史新高，地缘风险+降息预期双重驱动。央行持续增持黄金，实物需求旺盛。短期或有获利回吐，但中期趋势向上。",
            "news": ["🔥 黄金突破2800美元 → 避险情绪+降息预期双重驱动"]
        },
        {
            "name": "芯片",
            "heat": 4,
            "direction": "利好",
            "analysis": "中芯国际领涨带动板块走强，国产替代逻辑持续演绎。先进制程突破+设备国产化加速，产业链景气度回升。关注业绩兑现情况。",
            "news": ["📰 中芯国际涨超5% → 国产替代加速，先进制程突破"]
        },
        {
            "name": "锂电池",
            "heat": 4,
            "direction": "利好",
            "analysis": "特斯拉交付超预期提振板块情绪，宁德时代新电池技术发布增强竞争力。锂电池价格企稳，产业链盈利有望修复。",
            "news": ["📰 特斯拉Q4交付超预期 → 新能源车需求韧性强"]
        },
        {
            "name": "证券",
            "heat": 3,
            "direction": "利好",
            "analysis": "券商股异动涨停，或预示市场情绪转暖。成交量能否放大是关键，若持续放量则券商弹性可期。",
            "news": ["📰 多只券商股涨停 → 市场情绪回暖信号"]
        },
    ],
    "risk_level": "中"
}

# 模拟 AI 板块映射结果（使用 etf_master.json 中的实际板块）
MOCK_SECTOR_MAPPING = {
    "黄金": ["黄金"],
    "芯片": ["芯片", "半导体"],
    "锂电池": ["锂电池", "汽车"],
    "证券": ["证券"],
}

# 模拟 ETF 实时数据
MOCK_FUND_DATA = {
    "518880": {"code": "518880", "name": "黄金ETF", "price": 10.93, "change_pct": 1.25, "amount_yi": 85.6},
    "159934": {"code": "159934", "name": "黄金ETF", "price": 5.12, "change_pct": 1.18, "amount_yi": 42.3},
    "159812": {"code": "159812", "name": "黄金9999", "price": 10.88, "change_pct": 1.22, "amount_yi": 28.1},
    "512480": {"code": "512480", "name": "半导体ETF", "price": 1.45, "change_pct": 3.21, "amount_yi": 65.2},
    "159995": {"code": "159995", "name": "芯片ETF", "price": 1.38, "change_pct": 2.98, "amount_yi": 58.7},
    "512760": {"code": "512760", "name": "芯片ETF", "price": 1.42, "change_pct": 3.05, "amount_yi": 45.3},
    "159755": {"code": "159755", "name": "电池ETF", "price": 0.85, "change_pct": 2.15, "amount_yi": 32.1},
    "516390": {"code": "516390", "name": "光伏ETF", "price": 0.72, "change_pct": 1.88, "amount_yi": 28.5},
    "159840": {"code": "159840", "name": "科创新能源ETF", "price": 0.68, "change_pct": 2.05, "amount_yi": 15.2},
    "512880": {"code": "512880", "name": "证券ETF", "price": 1.12, "change_pct": 4.52, "amount_yi": 125.8},
    "512000": {"code": "512000", "name": "券商ETF", "price": 1.08, "change_pct": 4.35, "amount_yi": 98.6},
    "159842": {"code": "159842", "name": "证券ETF", "price": 1.15, "change_pct": 4.28, "amount_yi": 35.2},
}


class MockNewsItem:
    """模拟新闻对象"""
    def __init__(self, source: str, title: str):
        self.source = source
        self.title = title
        self.url = f"https://example.com/{hash(title)}"
        self.published_at = datetime.now(timezone(timedelta(hours=8)))


def get_mock_news_items():
    """获取模拟新闻列表"""
    return [MockNewsItem(n["source"], n["title"]) for n in MOCK_NEWS]


async def mock_ai_analyze(items, sector_list=None, history_context=""):
    """模拟 AI 分析"""
    logger.info(f"[MOCK] AI 分析 {len(items)} 条新闻")
    return MOCK_ANALYSIS_RESULT


async def mock_ai_map_to_master_sectors(ai_sectors, master_sectors):
    """模拟 AI 板块映射"""
    logger.info(f"[MOCK] AI 映射 {len(ai_sectors)} 个板块")
    return {s: MOCK_SECTOR_MAPPING.get(s, []) for s in ai_sectors}


async def mock_batch_get_funds(codes):
    """模拟批量获取 ETF 数据"""
    logger.info(f"[MOCK] 获取 {len(codes)} 个 ETF 实时数据")
    return {c: MOCK_FUND_DATA[c] for c in codes if c in MOCK_FUND_DATA}


async def test_full_flow_with_mock():
    """测试完整流程（使用模拟数据）"""
    from src.worker_simple import enrich_sectors_with_etfs

    result = MOCK_ANALYSIS_RESULT.copy()
    result["sectors"] = [s.copy() for s in MOCK_ANALYSIS_RESULT["sectors"]]

    with patch("src.worker_simple.ai_map_to_master_sectors", mock_ai_map_to_master_sectors):
        with patch("src.worker_simple.fund_service.batch_get_funds", mock_batch_get_funds):
            await enrich_sectors_with_etfs(result)

    sectors = result["sectors"]
    assert len(sectors) == 4

    for sector in sectors:
        assert "etfs" in sector
        assert len(sector["etfs"]) > 0
        logger.info(f"✅ {sector['name']}: {[e['name'] for e in sector['etfs']]}")

    gold_sector = next(s for s in sectors if s["name"] == "黄金")
    assert gold_sector["etfs"][0]["name"] == "黄金ETF"

    logger.info("✅ 完整流程测试通过")


async def test_output_format():
    """测试输出格式"""
    result = MOCK_ANALYSIS_RESULT.copy()
    result["sectors"] = [s.copy() for s in MOCK_ANALYSIS_RESULT["sectors"]]

    with patch("src.worker_simple.ai_map_to_master_sectors", mock_ai_map_to_master_sectors):
        with patch("src.worker_simple.fund_service.batch_get_funds", mock_batch_get_funds):
            from src.worker_simple import enrich_sectors_with_etfs
            await enrich_sectors_with_etfs(result)

    beijing_tz = timezone(timedelta(hours=8))
    output = {
        "result": result,
        "updated_at": datetime.now(beijing_tz).isoformat(),
        "news_count": len(MOCK_NEWS),
        "source_stats": {"财联社": 2, "东方财富": 2, "华尔街见闻": 2, "金十数据": 2},
    }

    json_str = json.dumps(output, ensure_ascii=False, indent=2)
    assert len(json_str) > 0

    parsed = json.loads(json_str)
    assert "result" in parsed
    assert "market_view" in parsed["result"]
    assert "sectors" in parsed["result"]

    for sector in parsed["result"]["sectors"]:
        assert "name" in sector
        assert "etfs" in sector

    logger.info("✅ 输出格式测试通过")
    logger.info(f"输出大小: {len(json_str)} 字节")


def test_mock_data_consistency():
    """测试模拟数据一致性"""
    # 验证映射的板块都存在
    for sector, mapped in MOCK_SECTOR_MAPPING.items():
        assert len(mapped) > 0, f"{sector} 没有映射到任何板块"
    logger.info("✅ 模拟数据一致性测试通过")


if __name__ == "__main__":
    # 直接运行测试
    asyncio.run(test_full_flow_with_mock())
    asyncio.run(test_output_format())
    test_mock_data_consistency()
    print("\n✅ 所有测试通过")
