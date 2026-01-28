// ETF 行情服务 - 调用东方财富 API
import type { EtfData } from '../types'

const EASTMONEY_API = 'https://push2.eastmoney.com/api/qt/ulist.np/get'

// 获取交易所前缀
function getSecid(code: string): string {
  const prefix = code.startsWith('15') || code.startsWith('16') ? '0' : '1'
  return `${prefix}.${code}`
}

// 批量获取 ETF 实时行情
export async function fetchFunds(codes: string[]): Promise<Record<string, EtfData>> {
  if (!codes.length) return {}

  const secids = codes.map(getSecid).join(',')
  const params = new URLSearchParams({
    secids,
    fields: 'f12,f14,f2,f3,f5,f6,f15,f16,f17,f18',
    ut: 'fa5fd1943c7b386f172d6893dbfba10b'
  })

  const resp = await fetch(`${EASTMONEY_API}?${params}`)
  const json = await resp.json() as any

  const result: Record<string, EtfData> = {}
  for (const item of json.data?.diff || []) {
    result[item.f12] = {
      code: item.f12,
      name: item.f14,
      price: item.f2 / 1000,
      change_pct: item.f3 / 100,
      change_5d: 0,
      change_20d: 0,
      amount_yi: item.f6 / 100000000,
      flow_yi: 0,
      turnover: 0,
      kline: []
    }
  }
  return result
}
