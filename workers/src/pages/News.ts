import type { NewsItem } from '../types'
import { esc } from '../types'
import { styles } from './styles'

// 格式化时间
function formatTime(dateStr: string): string {
  const d = new Date(dateStr)
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const min = d.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}

// 新闻页样式
const newsStyles = `
.news-list { list-style: none; }
.news-item { padding: 12px 0; border-bottom: 1px solid #eee; }
.news-item:last-child { border-bottom: none; }
.news-title { font-size: 14px; color: #333; text-decoration: none; display: block; margin-bottom: 4px; }
.news-title:hover { color: #0066cc; }
.news-meta { font-size: 12px; color: #888; }
.news-source { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; margin-right: 8px; }
.filter-bar { margin-bottom: 16px; }
.filter-bar a { font-size: 13px; color: #666; text-decoration: none; margin-right: 12px; padding: 4px 8px; border-radius: 4px; }
.filter-bar a:hover, .filter-bar a.active { background: #e5e7eb; color: #333; }
`

// 渲染新闻页
export function renderNews(news: NewsItem[], source?: string | null): string {
  const newsListHtml = news.map(item => `
    <li class="news-item">
      <a class="news-title" href="${esc(item.url)}" target="_blank">${esc(item.title)}</a>
      <div class="news-meta">
        <span class="news-source">${esc(item.source)}</span>
        <span>${formatTime(item.published_at)}</span>
      </div>
    </li>
  `).join('')

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>新闻列表 - ETF风向标</title>
  <style>${styles}${newsStyles}</style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <h1>ETF风向标</h1>
      </div>
      <div class="meta">
        <a href="/">← 返回首页</a>
      </div>
    </header>

    <div class="card">
      <h2>新闻列表${source ? ` - ${esc(source)}` : ''}</h2>
      <div class="filter-bar">
        <a href="/news" class="${!source ? 'active' : ''}">全部</a>
      </div>
      <ul class="news-list">
        ${newsListHtml || '<li class="news-item">暂无新闻</li>'}
      </ul>
    </div>
  </div>
</body>
</html>`
}
