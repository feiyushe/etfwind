"""企业微信 Webhook 推送"""

import httpx
from loguru import logger
from typing import Optional
from datetime import datetime


def format_analysis_message(data: dict) -> str:
    """
    将分析结果格式化为企业微信 Markdown 消息

    Args:
        data: latest.json 的内容

    Returns:
        格式化后的 Markdown 字符串
    """
    result = data.get("result", {})
    updated_at = data.get("updated_at", "")
    news_count = data.get("news_count", 0)

    # 解析时间
    time_str = ""
    if updated_at:
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            time_str = dt.strftime("%m-%d %H:%M")
        except:
            time_str = updated_at[:16]

    lines = []

    # 标题
    market_view = result.get("market_view", "")
    lines.append(f"## {market_view}")
    lines.append("")

    # 摘要
    summary = result.get("summary", "")
    if summary:
        lines.append(summary)
        lines.append("")

    # 板块信号
    sectors = result.get("sectors", [])
    if sectors:
        lines.append("### 板块信号")
        for sector in sectors[:6]:  # 最多显示6个板块
            name = sector.get("name", "")
            signal = sector.get("signal", "")
            direction = sector.get("direction", "")
            heat = sector.get("heat", 0)
            heat_stars = "🔥" * min(heat, 5)

            # 信号颜色标记
            if "买入" in signal:
                signal_mark = "🟢"
            elif "回避" in signal:
                signal_mark = "🔴"
            else:
                signal_mark = "🟡"

            lines.append(f"> {signal_mark} **{name}** {heat_stars} {direction}")

            # 检查清单
            checklist = sector.get("checklist", [])
            if checklist:
                lines.append(f">    {' '.join(checklist[:3])}")

        lines.append("")

    # 风险提示
    risk_alerts = result.get("risk_alerts", [])
    if risk_alerts:
        lines.append("### ⚠️ 风险提示")
        for alert in risk_alerts[:3]:
            lines.append(f"> {alert}")
        lines.append("")

    # 机会提示
    opportunity_hints = result.get("opportunity_hints", [])
    if opportunity_hints:
        lines.append("### 💡 机会提示")
        for hint in opportunity_hints[:3]:
            lines.append(f"> {hint}")
        lines.append("")

    # 底部信息
    lines.append(f"---")
    lines.append(f"📊 基于 {news_count} 条新闻分析 | {time_str}")
    lines.append(f"🔗 [查看详情](https://etf.aurora-bots.com/)")

    return "\n".join(lines)


async def send_wechat_message(
    webhook_url: str,
    content: str,
    msg_type: str = "markdown"
) -> bool:
    """
    发送企业微信消息

    Args:
        webhook_url: 企业微信机器人 Webhook URL
        content: 消息内容
        msg_type: 消息类型 (markdown/text)

    Returns:
        是否发送成功
    """
    if not webhook_url:
        logger.warning("企业微信 Webhook URL 未配置")
        return False

    payload = {
        "msgtype": msg_type,
        msg_type: {"content": content}
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(webhook_url, json=payload)
            data = resp.json()

            if data.get("errcode") == 0:
                logger.info("企业微信推送成功")
                return True
            else:
                logger.error(f"企业微信推送失败: {data}")
                return False
    except Exception as e:
        logger.error(f"企业微信推送异常: {e}")
        return False
