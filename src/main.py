"""主程序入口"""

import asyncio
import sys

import click
from loguru import logger

from src.collectors import NewsAggregator
from src.analyzers import ClaudeAnalyzer
from src.publishers import WeComPublisher, EmailPublisher, LocalReportGenerator
from src.models import InvestmentReport
from src.web.database import init_db, save_report


# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO",
)


async def run(period: str, print_report: bool = False, save_local: bool = False):
    """运行主流程"""
    logger.info(f"开始执行 {period} 任务")

    # 1. 采集新闻
    aggregator = NewsAggregator()
    try:
        news = await aggregator.collect_all()
        logger.info(f"采集完成，共 {news.count} 条新闻")

        if news.count == 0:
            logger.warning("未采集到任何新闻，退出")
            return
    finally:
        await aggregator.close()

    # 2. AI 分析
    analyzer = ClaudeAnalyzer()
    report = await analyzer.analyze(news, period)
    logger.info("AI 分析完成")

    # 打印报告到控制台
    if print_report:
        print_report_to_console(report)

    # 生成本地报告
    if save_local:
        generator = LocalReportGenerator()
        paths = generator.generate(report)
        logger.info(f"本地报告: {paths}")

    # 保存到数据库
    await init_db()
    report_id = await save_report(report)
    logger.info(f"报告已保存到数据库, ID: {report_id}")

    # 3. 推送
    wecom = WeComPublisher()
    email = EmailPublisher()

    results = await asyncio.gather(
        wecom.publish(report),
        email.publish(report),
        return_exceptions=True,
    )

    success_count = sum(1 for r in results if r is True)
    logger.info(f"推送完成，成功 {success_count}/{len(results)}")


def print_report_to_console(report: InvestmentReport):
    """打印报告到控制台"""
    period_name = "早盘分析" if report.period == "morning" else "晚盘总结"
    time_str = report.generated_at.strftime("%Y-%m-%d %H:%M")

    print("\n" + "=" * 60)
    print(f"📊 {period_name} ({time_str})")
    print("=" * 60)

    print("\n【市场概览】")
    print(report.market_overview.summary)

    if report.market_overview.key_events:
        print("\n【重要事件】")
        for event in report.market_overview.key_events:
            print(f"  • {event}")

    if report.market_overview.risk_factors:
        print("\n【风险提示】")
        for risk in report.market_overview.risk_factors:
            print(f"  ⚠️ {risk}")

    print("\n【基金建议】")
    for advice in report.fund_advices:
        emoji = {"看多": "🟢", "看空": "🔴", "观望": "🟡"}.get(advice.sentiment.value, "⚪")
        print(f"\n  {advice.fund_type.value} {emoji} {advice.sentiment.value}")
        print(f"    {advice.reason}")

    print("\n" + "-" * 60)
    print(f"⚠️ {report.disclaimer}")
    print("=" * 60 + "\n")


@click.command()
@click.option(
    "--period",
    type=click.Choice(["morning", "evening"]),
    default="morning",
    help="报告周期: morning=早盘, evening=晚盘",
)
@click.option(
    "--print",
    "print_report",
    is_flag=True,
    help="打印报告到控制台",
)
@click.option(
    "--save",
    "save_local",
    is_flag=True,
    help="保存本地 HTML/PDF 报告",
)
def main(period: str, print_report: bool, save_local: bool):
    """每日财经新闻收集与基金投资建议系统"""
    asyncio.run(run(period, print_report, save_local))


if __name__ == "__main__":
    main()
