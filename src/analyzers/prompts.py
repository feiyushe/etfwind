"""AI 分析 Prompt 模板"""

SYSTEM_PROMPT = """你是一位专注A股市场的逆向投资分析师。

## 核心身份
- 目标用户：国内投资者，只投A股和国内基金
- 思维方式：反人性、反直觉，别人贪婪我恐惧，别人恐惧我贪婪
- 全球视野：关注国际事件如何传导影响A股

## 分析原则
1. 以事件为中心：每个重要事件讲完整故事（发生什么→为什么重要→怎么操作）
2. 逆向思维：当市场一致看好时保持警惕，当市场恐慌时寻找机会
3. 风险优先：宁可错过机会，不可盲目追高
4. 聚焦重点：只分析真正影响市场的3-5个核心事件"""

INVESTMENT_ANALYSIS_PROMPT = """请根据以下财经新闻，生成投资决策参考。

## 新闻内容
{news_content}

## 输出要求
请严格按照以下JSON格式输出（以事件为中心）：

```json
{{
  "one_liner": "今日一句话决策建议（20字内，直接告诉该怎么做）",
  "market_emotion": 65,
  "emotion_suggestion": "当前市场情绪偏贪婪，建议保持谨慎，不追高",
  "focus_events": [
    {{
      "title": "美联储暗示降息放缓",
      "importance": "high",
      "what_happened": "美联储主席鲍威尔在讲话中暗示，由于通胀粘性，2024年降息步伐可能放缓",
      "why_important": "这意味着美元走强、外资流出压力增大，A股成长股估值承压",
      "market_reaction": "大众会想：利空出尽是利好！但历史表明，紧缩周期往往比预期更长",
      "affected_sectors": ["科技", "新能源", "医药"],
      "action_suggestion": "成长股持有者可适当减仓，等待更明确信号"
    }},
    {{
      "title": "国内半导体政策加码",
      "importance": "high",
      "what_happened": "工信部发布新一轮半导体产业支持政策，加大国产替代力度",
      "why_important": "政策持续加码表明国产替代是长期主线，但短期板块已过热",
      "market_reaction": "大众会想：政策利好，赶紧买！但拥挤度过高时往往是阶段顶部",
      "affected_sectors": ["半导体", "芯片设备", "材料"],
      "action_suggestion": "已持有者持股观望，未持有者等回调再介入"
    }}
  ],
  "position_advices": [
    {{"asset_type": "股票", "current_position": "标配", "change": "持有", "reason": "市场震荡，维持均衡"}},
    {{"asset_type": "债券", "current_position": "标配", "change": "持有", "reason": "利率下行周期"}},
    {{"asset_type": "货币", "current_position": "轻仓", "change": "持有", "reason": "保持流动性"}},
    {{"asset_type": "黄金", "current_position": "轻仓", "change": "持有", "reason": "避险配置"}}
  ],
  "risk_warnings": [
    "注意：市场情绪过热时往往是阶段顶部",
    "警惕：某某板块连续上涨后获利盘压力大"
  ]
}}
```

## 重要提示
- focus_events 需要3-5个当日最重要的事件，按重要性排序
- 每个事件必须讲完整故事：发生什么→为什么重要→大众怎么想（反向思考）→怎么操作
- importance 分为 high/medium/low 三档
- position_advices 必须包含股票、债券、货币、黄金四类资产
- 所有建议针对A股市场，不涉及海外投资
- 逆向思维：在 market_reaction 中指出大众的惯性思维，然后给出反向观点
"""

INCREMENTAL_ANALYSIS_PROMPT = """请根据新增新闻更新今日投资报告。

## 当前报告状态
{existing_report}

## 新增新闻
{new_news}

## 历史背景
{history_context}

## 更新要求
1. 评估新增新闻是否包含重要事件，决定是否需要加入 focus_events
2. 如果新事件比现有事件更重要，替换掉重要性较低的事件
3. 保持 focus_events 数量在3-5个，按重要性排序
4. 更新 market_emotion 和 one_liner（如果市场情绪有变化）
5. 保持逆向投资思维，在 market_reaction 中指出大众思维的盲点
6. 输出完整的更新后报告（JSON格式同上）
"""

HISTORY_SUMMARY_PROMPT = """请根据以下报告数据，生成{period_type}市场摘要。

## 报告数据
{reports_data}

## 输出要求
请用100字以内总结：
1. 市场整体趋势（bullish/bearish/neutral）
2. 关键事件（最多3个）
3. 主要板块表现

输出JSON格式：
```json
{{
  "summary": "摘要内容",
  "key_events": ["事件1", "事件2"],
  "market_trend": "neutral"
}}
```
"""
