import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { blogAPI } from '../../api/modules/blog.api'
import { useAuthStore } from '../../store/authStore'
import { colors } from '../../utils/styles'

function BlogCard({ blog, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: '1.25rem 1.5rem',
        background: '#fff',
        borderRadius: 8,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        cursor: 'pointer',
        transition: 'transform 0.15s, box-shadow 0.15s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)'
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.08)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}>
        <h3 style={{ margin: 0, color: colors.text, fontSize: '1.15rem' }}>{blog.title}</h3>
        {blog.is_public && (
          <span style={{ fontSize: 12, color: colors.success, padding: '2px 8px', background: '#e6f7eb', borderRadius: 12 }}>
            公开
          </span>
        )}
      </div>
      <p style={{ color: colors.textMuted, marginTop: 8, marginBottom: 8, fontSize: '0.95rem' }}>
        {blog.content.slice(0, 120)}{blog.content.length > 120 ? '…' : ''}
      </p>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {(blog.tags || []).map((t) => (
            <span key={t} style={{ fontSize: 12, padding: '2px 8px', background: '#f0f0f0', borderRadius: 4, color: colors.textMuted }}>
              #{t}
            </span>
          ))}
        </div>
        <span style={{ fontSize: 12, color: colors.textMuted }}>
          {new Date(blog.created_at).toLocaleString('zh-CN')}
        </span>
      </div>
    </div>
  )
}

function BlogList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [tag, setTag] = useState('')
  const [searchInput, setSearchInput] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['blogs', { page, search, tag }],
    queryFn: async () => {
      const params = { page, page_size: 10 }
      if (search) params.search = search
      if (tag) params.tag = tag
      const res = await blogAPI.getBlogs(params)
      return res.data || res
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => blogAPI.deleteBlog(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['blogs'] }),
  })

  const handleSearch = () => {
    setPage(1)
    setSearch(searchInput)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('确定要删除这篇博客吗？')) return
    try {
      await deleteMutation.mutateAsync(id)
    } catch (e) {
      alert('删除失败: ' + e.message)
    }
  }

  // 从所有博客聚合出唯一标签列表
  const allTags = Array.from(
    new Set((data?.items || []).flatMap((b) => b.tags || []))
  )

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0 }}>我的博客</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link to="/profile" style={{ padding: '0.5rem 1rem', color: colors.primary, textDecoration: 'none' }}>
            {user?.nickname || user?.username}
          </Link>
          <button
            onClick={() => navigate('/blogs/new')}
            style={{
              padding: '0.5rem 1rem', background: colors.primary, color: 'white',
              border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: '0.95rem',
            }}
          >
            ＋ 新建博客
          </button>
        </div>
      </div>

      <div style={{
        display: 'flex', gap: 8, marginBottom: '1.5rem', flexWrap: 'wrap',
        padding: '1rem', background: '#fff', borderRadius: 8,
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      }}>
        <input
          type="text" placeholder="搜索标题或内容…"
          value={searchInput} onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          style={{
            flex: 1, minWidth: 200, padding: '0.5rem 0.75rem',
            border: `1px solid ${colors.border}`, borderRadius: 4, fontSize: '0.95rem',
          }}
        />
        <button onClick={handleSearch} style={{
          padding: '0.5rem 1rem', background: colors.primary, color: 'white',
          border: 'none', borderRadius: 4, cursor: 'pointer',
        }}>搜索</button>
        {tag && (
          <button onClick={() => { setTag(''); setPage(1) }} style={{
            padding: '0.5rem 1rem', background: '#6c757d', color: 'white',
            border: 'none', borderRadius: 4, cursor: 'pointer',
          }}>
            清除标签 #{tag}
          </button>
        )}
      </div>

      {allTags.length > 0 && (
        <div style={{ marginBottom: '1.5rem', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {allTags.map((t) => (
            <button
              key={t}
              onClick={() => { setTag(t); setPage(1) }}
              style={{
                fontSize: 12, padding: '4px 10px',
                background: tag === t ? colors.primary : '#fff',
                color: tag === t ? 'white' : colors.text,
                border: `1px solid ${tag === t ? colors.primary : colors.border}`,
                borderRadius: 12, cursor: 'pointer',
              }}
            >
              #{t}
            </button>
          ))}
        </div>
      )}

      {isLoading && <p style={{ textAlign: 'center', color: colors.textMuted }}>加载中…</p>}
      {error && <p style={{ color: colors.danger }}>加载失败: {error.message}</p>}

      {!isLoading && (data?.items?.length ?? 0) === 0 && (
        <div style={{
          textAlign: 'center', padding: '3rem', background: '#fff',
          borderRadius: 8, color: colors.textMuted,
        }}>
          <p>还没有博客，<Link to="/blogs/new" style={{ color: colors.primary }}>写第一篇</Link>吧 ✍️</p>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {(data?.items || []).map((blog) => (
          <div key={blog.id} style={{ position: 'relative' }}>
            <BlogCard blog={blog} onClick={() => navigate(`/blogs/${blog.id}`)} />
            <div style={{ position: 'absolute', top: 12, right: 12, display: 'flex', gap: 4 }}>
              <button
                onClick={(e) => { e.stopPropagation(); navigate(`/blogs/${blog.id}/edit`) }}
                title="编辑"
                style={{
                  padding: '2px 8px', fontSize: 12, background: '#f0f0f0',
                  border: 'none', borderRadius: 4, cursor: 'pointer', color: colors.textMuted,
                }}
              >
                编辑
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); handleDelete(blog.id) }}
                title="删除"
                style={{
                  padding: '2px 8px', fontSize: 12, background: '#fde8e8',
                  border: 'none', borderRadius: 4, cursor: 'pointer', color: colors.danger,
                }}
              >
                删除
              </button>
            </div>
          </div>
        ))}
      </div>

      {(data?.total_pages ?? 0) > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: '1.5rem' }}>
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
            style={{ padding: '0.4rem 0.8rem', border: `1px solid ${colors.border}`, background: '#fff', borderRadius: 4, cursor: page === 1 ? 'not-allowed' : 'pointer' }}
          >
            上一页
          </button>
          <span style={{ padding: '0.4rem 0.8rem', color: colors.textMuted }}>
            {page} / {data.total_pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))} disabled={page >= data.total_pages}
            style={{ padding: '0.4rem 0.8rem', border: `1px solid ${colors.border}`, background: '#fff', borderRadius: 4, cursor: page >= data.total_pages ? 'not-allowed' : 'pointer' }}
          >
            下一页
          </button>
        </div>
      )}
    </div>
  )
}

export default BlogList
