import { useNavigate, useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { blogAPI } from '../../api/modules/blog.api'
import { useAuthStore } from '../../store/authStore'
import { MarkdownView } from '../../utils/markdown'
import { colors } from '../../utils/styles'

function BlogDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()

  const { data: blog, isLoading, error } = useQuery({
    queryKey: ['blog', id],
    queryFn: async () => {
      const res = await blogAPI.getBlog(id)
      return res.data || res
    },
    enabled: !!id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => blogAPI.deleteBlog(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blogs'] })
      navigate('/blogs')
    },
  })

  const handleDelete = () => {
    if (window.confirm('确定要删除这篇博客吗？此操作不可恢复')) {
      deleteMutation.mutate()
    }
  }

  if (isLoading) return <p style={{ textAlign: 'center', padding: '3rem' }}>加载中…</p>
  if (error) return <p style={{ color: colors.danger, padding: '2rem' }}>加载失败: {error.message}</p>
  if (!blog) return null

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <Link to="/blogs" style={{ color: colors.primary, textDecoration: 'none' }}>← 返回列表</Link>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => navigate(`/blogs/${id}/edit`)}
            style={{
              padding: '0.4rem 1rem', background: '#fff',
              border: `1px solid ${colors.primary}`, color: colors.primary,
              borderRadius: 4, cursor: 'pointer',
            }}
          >
            编辑
          </button>
          <button
            onClick={handleDelete}
            disabled={deleteMutation.isLoading}
            style={{
              padding: '0.4rem 1rem', background: colors.danger, color: 'white',
              border: 'none', borderRadius: 4,
              cursor: deleteMutation.isLoading ? 'not-allowed' : 'pointer',
            }}
          >
            {deleteMutation.isLoading ? '删除中…' : '删除'}
          </button>
        </div>
      </div>

      <article style={{
        background: '#fff', padding: '2rem', borderRadius: 8,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
      }}>
        <h1 style={{ marginTop: 0, color: colors.text }}>{blog.title}</h1>
        <div style={{
          display: 'flex', gap: 12, alignItems: 'center',
          color: colors.textMuted, fontSize: '0.9rem', marginBottom: '1.5rem',
        }}>
          <span>{user?.nickname || user?.username}</span>
          <span>·</span>
          <span>{new Date(blog.created_at).toLocaleString('zh-CN')}</span>
          {blog.updated_at && blog.updated_at !== blog.created_at && (
            <>
              <span>·</span>
              <span>更新于 {new Date(blog.updated_at).toLocaleString('zh-CN')}</span>
            </>
          )}
          {blog.is_public ? (
            <span style={{ marginLeft: 'auto', color: colors.success }}>● 公开</span>
          ) : (
            <span style={{ marginLeft: 'auto', color: colors.textMuted }}>● 私密</span>
          )}
        </div>
        {(blog.tags || []).length > 0 && (
          <div style={{ marginBottom: '1.5rem', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {blog.tags.map((t) => (
              <span key={t} style={{
                fontSize: 12, padding: '2px 10px', background: '#f0f0f0',
                borderRadius: 12, color: colors.textMuted,
              }}>
                #{t}
              </span>
            ))}
          </div>
        )}
        <hr style={{ border: 'none', borderTop: `1px solid ${colors.border}`, margin: '1.5rem 0' }} />
        <MarkdownView source={blog.content} />
      </article>
    </div>
  )
}

export default BlogDetail
