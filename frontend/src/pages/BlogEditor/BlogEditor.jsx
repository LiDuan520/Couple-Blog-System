import { useState, useEffect } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { blogAPI } from '../../api/modules/blog.api'
import { MarkdownView } from '../../utils/markdown'
import {
  colors, buttonStyle, inputStyle, labelStyle, formGroupStyle, errorTextStyle,
} from '../../utils/styles'

const EMPTY_DRAFT = { title: '', content: '', tags: [], is_public: false }

function BlogEditor() {
  const { id } = useParams()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [form, setForm] = useState(EMPTY_DRAFT)
  const [tagInput, setTagInput] = useState('')
  const [showPreview, setShowPreview] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const { data: existing, isLoading } = useQuery({
    queryKey: ['blog', id],
    queryFn: async () => {
      const res = await blogAPI.getBlog(id)
      return res.data || res
    },
    enabled: isEdit,
  })

  useEffect(() => {
    if (existing) {
      setForm({
        title: existing.title || '',
        content: existing.content || '',
        tags: existing.tags || [],
        is_public: !!existing.is_public,
      })
    }
  }, [existing])

  const saveMutation = useMutation({
    mutationFn: async (payload) => {
      if (isEdit) return blogAPI.updateBlog(id, payload)
      return blogAPI.createBlog(payload)
    },
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['blogs'] })
      const data = res.data || res
      navigate(`/blogs/${data.id}`)
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    setErrorMsg('')
    if (!form.title.trim()) { setErrorMsg('标题不能为空'); return }
    if (!form.content.trim()) { setErrorMsg('内容不能为空'); return }
    if (form.title.length > 200) { setErrorMsg('标题不能超过 200 字'); return }
    if (form.content.length > 10000) { setErrorMsg('内容不能超过 10000 字'); return }
    saveMutation.mutate(form)
  }

  const addTag = () => {
    const t = tagInput.trim()
    if (!t) return
    if (t.length > 20) { setErrorMsg('单个标签最多 20 字'); return }
    if (form.tags.length >= 10) { setErrorMsg('最多 10 个标签'); return }
    if (!form.tags.includes(t)) {
      setForm((p) => ({ ...p, tags: [...p.tags, t] }))
    }
    setTagInput('')
  }
  const removeTag = (t) => setForm((p) => ({ ...p, tags: p.tags.filter((x) => x !== t) }))

  if (isEdit && isLoading) {
    return <p style={{ textAlign: 'center', padding: '3rem' }}>加载中…</p>
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0 }}>{isEdit ? '编辑博客' : '写新博客'}</h1>
        <Link to="/blogs" style={{ color: colors.primary, textDecoration: 'none' }}>← 返回列表</Link>
      </div>

      <form onSubmit={handleSubmit} style={{
        background: '#fff', padding: '1.5rem', borderRadius: 8,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
      }}>
        <div style={formGroupStyle}>
          <label style={labelStyle}>标题</label>
          <input
            name="title" value={form.title}
            onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
            style={inputStyle(false)} maxLength={200}
            placeholder="给你的博客起个名字…"
          />
          <div style={{ fontSize: 12, color: colors.textMuted, textAlign: 'right' }}>
            {form.title.length} / 200
          </div>
        </div>

        <div style={formGroupStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <label style={labelStyle}>内容（支持 Markdown）</label>
            <button
              type="button" onClick={() => setShowPreview((v) => !v)}
              style={{ fontSize: 12, padding: '4px 10px', background: '#f0f0f0', border: 'none', borderRadius: 4, cursor: 'pointer' }}
            >
              {showPreview ? '编辑' : '预览'}
            </button>
          </div>
          {showPreview ? (
            <div style={{
              minHeight: 320, padding: '1rem', border: `1px solid ${colors.border}`,
              borderRadius: 4, background: '#fafafa',
            }}>
              <MarkdownView source={form.content || '（暂无内容）'} />
            </div>
          ) : (
            <textarea
              value={form.content}
              onChange={(e) => setForm((p) => ({ ...p, content: e.target.value }))}
              style={{
                ...inputStyle(false),
                minHeight: 320, fontFamily: 'Menlo, Consolas, monospace',
                fontSize: '0.95rem', resize: 'vertical',
              }}
              maxLength={10000}
              placeholder="# 标题&#10;&#10;用 Markdown 写下你的故事…"
            />
          )}
          <div style={{ fontSize: 12, color: colors.textMuted, textAlign: 'right' }}>
            {form.content.length} / 10000
          </div>
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>标签</label>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
            {form.tags.map((t) => (
              <span key={t} style={{
                fontSize: 12, padding: '4px 10px', background: '#e6f0ff',
                color: colors.primary, borderRadius: 12,
                display: 'inline-flex', alignItems: 'center', gap: 4,
              }}>
                #{t}
                <button
                  type="button" onClick={() => removeTag(t)}
                  style={{ background: 'none', border: 'none', color: colors.primary, cursor: 'pointer', padding: 0, fontSize: 14 }}
                >×</button>
              </span>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text" value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
              placeholder="输入标签后回车" maxLength={20}
              style={{ ...inputStyle(false), flex: 1 }}
            />
            <button
              type="button" onClick={addTag}
              style={{ padding: '0.5rem 1rem', background: colors.textMuted, color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
            >
              添加
            </button>
          </div>
        </div>

        <div style={{ ...formGroupStyle, display: 'flex', alignItems: 'center' }}>
          <input
            type="checkbox" id="is_public"
            checked={form.is_public}
            onChange={(e) => setForm((p) => ({ ...p, is_public: e.target.checked }))}
            style={{ marginRight: 8 }}
          />
          <label htmlFor="is_public" style={{ color: colors.text, cursor: 'pointer' }}>
            公开（其他登录用户可查看）
          </label>
        </div>

        {errorMsg && <div style={{ ...errorTextStyle, marginBottom: '1rem' }}>{errorMsg}</div>}
        {saveMutation.isError && (
          <div style={{ ...errorTextStyle, marginBottom: '1rem' }}>
            保存失败: {saveMutation.error?.message}
          </div>
        )}

        <div style={{ display: 'flex', gap: 8 }}>
          <button
            type="submit" disabled={saveMutation.isLoading}
            style={{ ...buttonStyle('primary', saveMutation.isLoading), width: 'auto', flex: 1 }}
          >
            {saveMutation.isLoading ? '保存中…' : (isEdit ? '更新' : '发布')}
          </button>
          <button
            type="button" onClick={() => navigate('/blogs')}
            style={{ ...buttonStyle('primary', false), width: 'auto', flex: 1, background: '#6c757d' }}
          >
            取消
          </button>
        </div>
      </form>
    </div>
  )
}

export default BlogEditor
