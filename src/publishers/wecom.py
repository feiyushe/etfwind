"""企业微信机器人推送"""

import httpx
from loguru import logger

from src.config import settings
from src.models import InvestmentReport


class WeComPublisher:
    """企业微信机器人推送"""

    def __init__(self):
        self.webhook_url = settings.wecom_webhook_url

    async def publish(self, report: InvestmentReport) -> bool:
        """推送报告到企业微信"""
        if not self.webhook_url:
            logger.warning("未配置企业微信 Webhook URL，跳过推送")
            return False

        content = self._format_markdown(report)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    json={
                        "msgtype": "markdown",
                        "markdown": {"content": content},
                    },
                )
                response.raise_for_status()
                result = response.json()

                if result.get("errcode") == 0:
                    logger.info("企业微信推送成功")
                    return True
                else:
                    logger.error(f"企业微信推送失败: {result}")
                    return False
            except Exception as e:
                logger.error(f"企业微信推送异常: {e}")
                return False

    def _format_markdown(self, report: InvestmentReport) -> str:
        """格式化为 Markdown"""
        period_name = "早盘分析" if report.period == "morning" else "晚盘总结"
        time_str = report.generated_at.strftime("%Y-%m-%d %H:%M")

        lines = [
            f"## 📊 {period_name}",
            f"> {time_str}",
            "",
            "### 市场概览",
            report.market_overview.summary,
            "",
        ]

        if report.market_overview.key_events:
            lines.append("**重要事件：**")
            for event in report.market_overview.key_events:
                lines.append(f"- {event}")
            lines.append("")

        if report.market_overview.risk_factors:
            lines.append("**风险提示：**")
            for risk in report.market_overview.risk_factors:
                lines.append(f"- ⚠️ {risk}")
            lines.append("")

        lines.append("### 基金建议")
        for advice in report.fund_advices:
            emoji = self._get_sentiment_emoji(advice.sentiment.value)
            lines.append(f"**{advice.fund_type.value}** {emoji} {advice.sentiment.value}")
            lines.append(f"> {advice.reason}")
            lines.append("")

        lines.append("---")
        lines.append(f"*{report.disclaimer}*")

        return "\n".join(lines)

    def _get_sentiment_emoji(self, sentiment: str) -> str:
        """获取情绪对应的 emoji"""
        return {"看多": "🟢", "看空": "🔴", "观望": "🟡"}.get(sentiment, "⚪")
