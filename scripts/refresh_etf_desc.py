"""重新生成 ETF 描述（基于现有数据）

用法：
    CLAUDE_API_KEY=xxx uv run python scripts/refresh_etf_desc.py
"""

import asyncio
import json
import os
from pathlib import Path

import httpx
from loguru import logger

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")


async def ai_generate_desc(client: httpx.AsyncClient, etf_infos: list[dict]) -> dict:
    """AI 批量生成 ETF 描述"""
    etf_list = "\n".join([
        f"- {info['code']} {info.get('name','')}: {info.get('scope','')[:150]}"
        for info in etf_infos
    ])

    prompt = f"""为以下ETF生成精炼描述和板块别名。

## ETF列表
{etf_list}

## 要求
1. desc: 20-30字描述，突出投资标的和特点，不要重复名称
2. tags: 3-5个板块别名，包含可能的叫法（如芯片ETF的tags: ["芯片", "半导体", "集成电路", "IC", "晶圆"]）

## 示例
- 黄金ETF → {{"desc": "跟踪上海金现货，对冲通胀和避险首选", "tags": ["黄金", "贵金属", "避险", "金价"]}}
- 芯片ETF → {{"desc": "覆盖半导体设计、制造、封测全产业链龙头", "tags": ["芯片", "半导体", "集成电路", "IC", "晶圆"]}}
- 证券ETF → {{"desc": "券商股打包投资，牛市弹性大", "tags": ["证券", "券商", "非银", "金融"]}}

## 输出JSON
```json
{{"ETF代码": {{"desc": "描述", "tags": ["别名1", "别名2", ...]}}, ...}}
```"""

    try:
        resp = await client.post(
            f"{CLAUDE_BASE_URL.rstrip('/')}/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=120,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text)
    except Exception as e:
        logger.warning(f"AI生成描述失败: {e}")
        return {}


async def main():
    if not CLAUDE_API_KEY:
        logger.error("请设置 CLAUDE_API_KEY")
        return

    # 读取现有数据
    master_file = Path(__file__).parent.parent / "config" / "etf_master.json"
    data = json.loads(master_file.read_text())
    etfs = data["etfs"]
    logger.info(f"读取到 {len(etfs)} 个 ETF")

    # 转为列表
    etf_list = list(etfs.values())

    # 批量生成描述
    all_descs = {}
    async with httpx.AsyncClient(timeout=120) as client:
        for i in range(0, len(etf_list), 30):
            batch = etf_list[i:i+30]
            logger.info(f"处理 {i+1}-{i+len(batch)}/{len(etf_list)}...")
            descs = await ai_generate_desc(client, batch)
            all_descs.update(descs)
            await asyncio.sleep(1)

    # 更新描述和tags
    updated = 0
    for code, info in all_descs.items():
        if code in etfs:
            if isinstance(info, dict):
                etfs[code]["desc"] = info.get("desc", "")
                etfs[code]["tags"] = info.get("tags", [])
            else:
                etfs[code]["desc"] = info
            updated += 1

    logger.info(f"更新了 {updated} 个描述")

    # 保存
    master_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    logger.info(f"已保存到 {master_file}")


if __name__ == "__main__":
    asyncio.run(main())
