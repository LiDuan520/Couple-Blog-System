import { useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { colors } from '../../utils/styles'

function Dashboard() {
  const navigate = useNavigate()
  const { user, logout, isAuthenticated } = useAuthStore()

  useEffect(() => {
    if (!isAuthenticated) navigate('/login')
  }, [isAuthenticated, navigate])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  if (!isAuthenticated) return null

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: '2rem',
      }}>
        <h1 style={{ margin: 0 }}>欢迎，{user?.nickname || user?.username} 👋</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link
            to="/profile"
            style={{
              padding: '0.5rem 1rem', background: '#fff',
              border: `1px solid ${colors.primary}`, color: colors.primary,
              borderRadius: 4, textDecoration: 'none', fontSize: '0.95rem',
            }}
          >
            个人资料
          </Link>
          <button
            onClick={handleLogout}
            style={{
              padding: '0.5rem 1rem', background: colors.danger, color: 'white',
              border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: '0.95rem',
            }}
          >
            登出
          </button>
        </div>
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1rem', marginTop: '1.5rem',
      }}>
        <Link
          to="/blogs"
          style={{
            padding: '2rem 1.5rem', background: '#fff', borderRadius: 8,
            boxShadow: '0 1px 3px rgba(0,0,0,0.08)', textDecoration: 'none',
            color: colors.text, transition: 'transform 0.15s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
        >
          <h3 style={{ margin: 0, color: colors.primary }}>📝 我的博客</h3>
          <p style={{ marginTop: 8, color: colors.textMuted, fontSize: '0.9rem' }}>
            查看、编辑、删除你写过的所有博客
          </p>
        </Link>
        <Link
          to="/blogs/new"
          style={{
            padding: '2rem 1.5rem', background: '#fff', borderRadius: 8,
            boxShadow: '0 1px 3px rgba(0,0,0,0.08)', textDecoration: 'none',
            color: colors.text, transition: 'transform 0.15s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
        >
          <h3 style={{ margin: 0, color: colors.success }}>✍️ 写新博客</h3>
          <p style={{ marginTop: 8, color: colors.textMuted, fontSize: '0.9rem' }}>
            用 Markdown 记录今天的回忆
          </p>
        </Link>
        <Link
          to="/profile"
          style={{
            padding: '2rem 1.5rem', background: '#fff', borderRadius: 8,
            boxShadow: '0 1px 3px rgba(0,0,0,0.08)', textDecoration: 'none',
            color: colors.text, transition: 'transform 0.15s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
        >
          <h3 style={{ margin: 0, color: colors.warning }}>👤 个人资料</h3>
          <p style={{ marginTop: 8, color: colors.textMuted, fontSize: '0.9rem' }}>
            修改昵称、头像、密码
          </p>
        </Link>
      </div>
    </div>
  )
}

export default Dashboard
