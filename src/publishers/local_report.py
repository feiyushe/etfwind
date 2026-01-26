"""本地报告生成器"""

import os
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.models import InvestmentReport


class LocalReportGenerator:
    """本地报告生成器"""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate(self, report: InvestmentReport) -> dict[str, str]:
        """生成 HTML 和 PDF 报告，返回文件路径"""
        date_str = report.generated_at.strftime("%Y%m%d_%H%M")
        base_name = f"investment_report_{report.period}_{date_str}"

        html_path = self._generate_html(report, base_name)
        pdf_path = self._generate_pdf(html_path, base_name)

        return {"html": str(html_path), "pdf": str(pdf_path) if pdf_path else None}

    def _generate_html(self, report: InvestmentReport, base_name: str) -> Path:
        """生成 HTML 报告"""
        html_path = self.output_dir / f"{base_name}.html"
        html_content = self._build_html(report)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML 报告已生成: {html_path}")
        return html_path

    def _generate_pdf(self, html_path: Path, base_name: str) -> Path | None:
        """生成 PDF 报告"""
        try:
            from weasyprint import HTML
            pdf_path = self.output_dir / f"{base_name}.pdf"
            HTML(filename=str(html_path)).write_pdf(str(pdf_path))
            logger.info(f"PDF 报告已生成: {pdf_path}")
            return pdf_path
        except ImportError:
            logger.warning("weasyprint 未安装，跳过 PDF 生成。安装: pip install weasyprint")
            return None
        except Exception as e:
            logger.error(f"PDF 生成失败: {e}")
            return None

    def _build_html(self, report: InvestmentReport) -> str:
        """构建 HTML 内容"""
        period_name = "早盘分析" if report.period == "morning" else "晚盘总结"
        time_str = report.generated_at.strftime("%Y-%m-%d %H:%M")

        # 构建基金建议卡片
        advices_html = self._build_advices_html(report.fund_advices)

        # 构建事件和风险列表
        events_html = "".join(f"<li>{e}</li>" for e in report.market_overview.key_events)
        risks_html = "".join(f"<li>{r}</li>" for r in report.market_overview.risk_factors)

        # 构建新闻来源列表
        sources_html = self._build_sources_html(report.news_sources)

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{period_name} - {time_str}</title>
    {self._get_styles()}
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 {period_name}</h1>
            <p class="time">{time_str}</p>
        </header>

        <section class="overview">
            <h2>市场概览</h2>
            <p class="summary">{report.market_overview.summary}</p>
        </section>

        <section class="events">
            <h2>📌 重要事件</h2>
            <ul>{events_html}</ul>
        </section>

        <section class="risks">
            <h2>⚠️ 风险提示</h2>
            <ul class="risk-list">{risks_html}</ul>
        </section>

        <section class="advices">
            <h2>💡 基金建议</h2>
            <div class="advice-grid">{advices_html}</div>
        </section>

        <section class="sources">
            <h2>📰 新闻来源</h2>
            <div class="sources-list">{sources_html}</div>
        </section>

        <footer>
            <p class="disclaimer">{report.disclaimer}</p>
        </footer>
    </div>
</body>
</html>"""

    def _build_advices_html(self, advices) -> str:
        """构建基金建议卡片 HTML"""
        cards = []
        for advice in advices:
            color = self._get_sentiment_color(advice.sentiment.value)
            emoji = self._get_sentiment_emoji(advice.sentiment.value)
            points = "".join(f"<li>{p}</li>" for p in advice.attention_points)

            card = f"""
            <div class="advice-card" style="border-left-color: {color};">
                <div class="advice-header">
                    <span class="fund-type">{advice.fund_type.value}</span>
                    <span class="sentiment" style="color: {color};">{emoji} {advice.sentiment.value}</span>
                </div>
                <p class="reason">{advice.reason}</p>
                <ul class="points">{points}</ul>
            </div>"""
            cards.append(card)
        return "".join(cards)

    def _get_sentiment_color(self, sentiment: str) -> str:
        """获取情绪颜色"""
        return {"看多": "#10b981", "看空": "#ef4444", "观望": "#f59e0b"}.get(sentiment, "#6b7280")

    def _get_sentiment_emoji(self, sentiment: str) -> str:
        """获取情绪 emoji"""
        return {"看多": "🟢", "看空": "🔴", "观望": "🟡"}.get(sentiment, "⚪")

    def _build_sources_html(self, news_sources) -> str:
        """构建新闻来源 HTML"""
        if not news_sources:
            return "<p>暂无新闻来源</p>"

        items = []
        for news in news_sources[:20]:
            time_str = ""
            if news.published_at:
                time_str = news.published_at.strftime("%H:%M")

            if news.url:
                link = f'<a href="{news.url}" target="_blank">{news.title}</a>'
            else:
                link = news.title

            items.append(f'''
            <div class="source-item">
                <span class="source-tag">{news.source}</span>
                <span class="source-time">{time_str}</span>
                <span class="source-title">{link}</span>
            </div>''')

        return "".join(items)

    def _get_styles(self) -> str:
        """获取 CSS 样式"""
        return """<style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f3f4f6; color: #1f2937; line-height: 1.6;
        }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        header { text-align: center; margin-bottom: 30px; }
        header h1 { font-size: 28px; color: #1e40af; margin-bottom: 8px; }
        header .time { color: #6b7280; font-size: 14px; }
        section { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        h2 { font-size: 18px; color: #374151; margin-bottom: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }
        .summary { font-size: 16px; color: #4b5563; }
        ul { padding-left: 20px; }
        li { margin-bottom: 8px; color: #4b5563; }
        .risk-list li { color: #dc2626; }
        .advice-grid { display: grid; gap: 16px; }
        .advice-card { background: #f9fafb; border-radius: 8px; padding: 16px; border-left: 4px solid; }
        .advice-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .fund-type { font-weight: 600; font-size: 16px; }
        .sentiment { font-weight: 600; }
        .reason { color: #4b5563; margin-bottom: 10px; }
        .points { font-size: 14px; color: #6b7280; }
        .sources-list { display: flex; flex-direction: column; gap: 8px; }
        .source-item { display: flex; align-items: center; gap: 10px; padding: 8px; background: #f9fafb; border-radius: 6px; }
        .source-tag { background: #e0e7ff; color: #3730a3; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; white-space: nowrap; }
        .source-time { color: #9ca3af; font-size: 12px; white-space: nowrap; }
        .source-title { flex: 1; font-size: 14px; }
        .source-title a { color: #2563eb; text-decoration: none; }
        .source-title a:hover { text-decoration: underline; }
        footer { text-align: center; padding: 20px; }
        .disclaimer { font-size: 12px; color: #9ca3af; font-style: italic; }
        @media print { body { background: white; } section { box-shadow: none; border: 1px solid #e5e7eb; } }
    </style>"""
