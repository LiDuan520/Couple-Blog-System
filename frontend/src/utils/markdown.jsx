// 极简 Markdown 渲染器（避免引入额外依赖）
// 支持：# 标题、**粗体**、*斜体*、`行内代码`、```代码块```、[链接](url)、- 列表、> 引用、--- 分隔
import React from 'react'

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderInline(text) {
  // 先做 HTML 转义，再做内联语法
  let html = escapeHtml(text)
  // 链接 [text](url)
  html = html.replace(
    /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
  )
  // 粗体
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  // 斜体
  html = html.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  return html
}

export function renderMarkdown(md) {
  if (!md) return ''
  const lines = md.split('\n')
  const out = []
  let inCode = false
  let codeBuf = []
  let inList = false
  let inQuote = false
  let quoteBuf = []

  const flushList = () => {
    if (inList) {
      out.push('</ul>')
      inList = false
    }
  }
  const flushQuote = () => {
    if (inQuote) {
      out.push(`<blockquote>${renderInline(quoteBuf.join(' '))}</blockquote>`)
      inQuote = false
      quoteBuf = []
    }
  }

  for (let line of lines) {
    if (line.startsWith('```')) {
      if (inCode) {
        out.push(`<pre><code>${escapeHtml(codeBuf.join('\n'))}</code></pre>`)
        codeBuf = []
        inCode = false
      } else {
        flushList(); flushQuote()
        inCode = true
      }
      continue
    }
    if (inCode) {
      codeBuf.push(line)
      continue
    }

    // 标题
    const hMatch = line.match(/^(#{1,6})\s+(.*)$/)
    if (hMatch) {
      flushList(); flushQuote()
      const level = hMatch[1].length
      out.push(`<h${level}>${renderInline(hMatch[2])}</h${level}>`)
      continue
    }

    // 水平线
    if (/^-{3,}$/.test(line.trim())) {
      flushList(); flushQuote()
      out.push('<hr/>')
      continue
    }

    // 列表
    if (/^[-*]\s+/.test(line)) {
      flushQuote()
      if (!inList) {
        out.push('<ul>')
        inList = true
      }
      out.push(`<li>${renderInline(line.replace(/^[-*]\s+/, ''))}</li>`)
      continue
    } else {
      flushList()
    }

    // 引用
    if (line.startsWith('> ')) {
      if (!inQuote) inQuote = true
      quoteBuf.push(line.slice(2))
      continue
    } else {
      flushQuote()
    }

    // 空行
    if (line.trim() === '') {
      continue
    }

    // 普通段落
    out.push(`<p>${renderInline(line)}</p>`)
  }
  flushList(); flushQuote()
  if (inCode) {
    out.push(`<pre><code>${escapeHtml(codeBuf.join('\n'))}</code></pre>`)
  }
  return out.join('\n')
}

export function MarkdownView({ source }) {
  return (
    <div
      className="markdown-body"
      style={{ lineHeight: 1.7, color: '#222' }}
      dangerouslySetInnerHTML={{ __html: renderMarkdown(source) }}
    />
  )
}
