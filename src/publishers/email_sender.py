"""邮件推送模块"""

import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib
from loguru import logger

from src.config import settings
from src.models import InvestmentReport


class EmailPublisher:
    """邮件推送"""

    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.recipients = settings.email_recipient_list

    async def publish(self, report: InvestmentReport) -> bool:
        """推送报告到邮件"""
        if not all([self.host, self.user, self.password, self.recipients]):
            logger.warning("邮件配置不完整，跳过推送")
            return False

        subject = self._get_subject(report)
        html_content = self._format_html(report)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.user
        msg["To"] = ", ".join(self.recipients)
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            context = ssl.create_default_context()
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                tls_context=context,
            )
            logger.info(f"邮件推送成功，收件人: {self.recipients}")
            return True
        except Exception as e:
            logger.error(f"邮件推送失败: {e}")
            return False

    def _get_subject(self, report: InvestmentReport) -> str:
        """生成邮件主题"""
        period_name = "早盘分析" if report.period == "morning" else "晚盘总结"
        date_str = report.generated_at.strftime("%Y-%m-%d")
        return f"【投资日报】{date_str} {period_name}"

    def _format_html(self, report: InvestmentReport) -> str:
        """格式化为 HTML"""
        period_name = "早盘分析" if report.period == "morning" else "晚盘总结"
        time_str = report.generated_at.strftime("%Y-%m-%d %H:%M")

        # 构建基金建议 HTML
        advices_html = ""
        for advice in report.fund_advices:
            color = self._get_sentiment_color(advice.sentiment.value)
            points_html = "".join(
                f"<li>{p}</li>" for p in advice.attention_points
            )
            advices_html += f"""
            <div style="margin-bottom:15px;padding:10px;border-left:3px solid {color};background:#f9f9f9;">
                <strong>{advice.fund_type.value}</strong>
                <span style="color:{color};font-weight:bold;margin-left:10px;">{advice.sentiment.value}</span>
                <p style="margin:8px 0;color:#666;">{advice.reason}</p>
                <ul style="margin:5px 0;padding-left:20px;color:#888;">{points_html}</ul>
            </div>
            """

        # 构建事件列表
        events_html = "".join(
            f"<li>{e}</li>" for e in report.market_overview.key_events
        )

        # 构建风险列表
        risks_html = "".join(
            f"<li style='color:#e74c3c;'>{r}</li>" for r in report.market_overview.risk_factors
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
            <h2 style="color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px;">
                📊 {period_name}
            </h2>
            <p style="color:#7f8c8d;font-size:12px;">{time_str}</p>

            <h3 style="color:#34495e;">市场概览</h3>
            <p style="line-height:1.6;">{report.market_overview.summary}</p>

            <h4 style="color:#2980b9;">重要事件</h4>
            <ul style="line-height:1.8;">{events_html}</ul>

            <h4 style="color:#c0392b;">风险提示</h4>
            <ul style="line-height:1.8;">{risks_html}</ul>

            <h3 style="color:#34495e;">基金建议</h3>
            {advices_html}

            <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
            <p style="color:#95a5a6;font-size:11px;font-style:italic;">
                {report.disclaimer}
            </p>
        </body>
        </html>
        """

    def _get_sentiment_color(self, sentiment: str) -> str:
        """获取情绪对应的颜色"""
        return {"看多": "#27ae60", "看空": "#e74c3c", "观望": "#f39c12"}.get(sentiment, "#95a5a6")
