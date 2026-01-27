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
请严格按照以下JSON格式输出：

```json
{{
  "one_liner": "今日一句话决策建议（20字内，直接告诉该怎么做）",
  "market_emotion": 65,
  "emotion_suggestion": "当前市场情绪偏贪婪，建议保持谨慎，不追高",
  "focus_events": [
    {{
      "title": "沪银夜盘暴涨超9%，贵金属情绪高涨",
      "sources": [
        {{"title": "沪银主力合约涨停", "url": "https://finance.sina.com.cn/..."}},
        {{"title": "白银期货创年内新高", "url": "https://www.cls.cn/..."}},
        {{"title": "贵金属板块全线走强", "url": "https://finance.eastmoney.com/..."}}
      ],
      "analysis": "据财联社报道，沪银夜盘涨幅罕见，单日涨超9%触及涨停。结合新浪财经数据，这一走势与全球避险情绪升温密切相关。从历史规律看，贵金属单日暴涨往往是短期情绪顶点，后续大概率进入震荡消化阶段。白银波动性远超黄金，当前追高风险较大。",
      "suggestion": "已持有白银相关标的者逢高减仓锁定利润，未持有者切勿追高",
      "importance": 1
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
- focus_events 需要8-10个当日最重要的事件，按重要性排序（importance: 1最重要）
- sources：每个事件附带2-3条相关新闻链接，直接使用新闻列表中提供的URL（格式为"标题 | URL"），优先选择国内源
- analysis：综合分析（100-150字），自然引用信息源，包含事件背景、市场影响、风险提示
- suggestion：一句话投资建议
- position_advices 必须包含股票、债券、货币、黄金四类资产
- 所有建议针对A股市场
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
2. 如果新事件比现有事件更重要，替换掉重要性较低的事件，调整 importance 排序
3. 保持 focus_events 数量在8-10个，按重要性排序（importance: 1最重要）
4. 每个事件格式：title、sources（2-3条国内新闻链接）、analysis（综合分析，引用信息源）、suggestion
5. 更新 market_emotion 和 one_liner（如果市场情绪有变化）
6. analysis 要自然流畅，引用具体信息源，避免"大众认为"等套话
7. 输出完整的更新后报告（JSON格式同上）
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
