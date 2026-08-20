import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { validateInput } from '../../utils/validation'
import {
  colors, buttonStyle, inputStyle, labelStyle, formGroupStyle, errorTextStyle,
} from '../../utils/styles'

function Login() {
  const navigate = useNavigate()
  const { login, isAuthenticated, isLoading, error, clearError } = useAuthStore()
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    remember_me: false,
  })
  const [showPassword, setShowPassword] = useState(false)
  const [touched, setTouched] = useState({})

  useEffect(() => {
    if (isAuthenticated) navigate('/')
  }, [isAuthenticated, navigate])

  useEffect(() => () => clearError(), [clearError])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData((p) => ({
      ...p,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleBlur = (field) => setTouched((p) => ({ ...p, [field]: true }))

  const errors = {
    username: formData.username && !validateInput.username(formData.username)
      ? '3-50 字符，仅字母数字下划线' : '',
    password: formData.password && formData.password.length < 8
      ? '至少 8 位' : '',
  }
  const hasError = Object.values(errors).some(Boolean)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setTouched({ username: true, password: true })
    if (hasError) return
    const result = await login(formData)
    if (result.success) navigate('/')
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '420px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '2rem', color: colors.text }}>
        登录
      </h1>
      <form onSubmit={handleSubmit} noValidate>
        <div style={formGroupStyle}>
          <label style={labelStyle}>用户名 / 邮箱</label>
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleChange}
            onBlur={() => handleBlur('username')}
            required
            style={inputStyle(touched.username && !!errors.username)}
            autoComplete="username"
          />
          {touched.username && errors.username && (
            <div style={errorTextStyle}>{errors.username}</div>
          )}
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>密码</label>
          <div style={{ position: 'relative' }}>
            <input
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={formData.password}
              onChange={handleChange}
              onBlur={() => handleBlur('password')}
              required
              style={inputStyle(touched.password && !!errors.password)}
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              style={{
                position: 'absolute', right: 8, top: '50%',
                transform: 'translateY(-50%)',
                background: 'none', border: 'none',
                color: colors.textMuted, cursor: 'pointer', fontSize: '0.85rem',
              }}
            >
              {showPassword ? '隐藏' : '显示'}
            </button>
          </div>
          {touched.password && errors.password && (
            <div style={errorTextStyle}>{errors.password}</div>
          )}
        </div>

        <div style={{ ...formGroupStyle, display: 'flex', alignItems: 'center' }}>
          <input
            type="checkbox"
            id="remember_me"
            name="remember_me"
            checked={formData.remember_me}
            onChange={handleChange}
            style={{ marginRight: 8 }}
          />
          <label htmlFor="remember_me" style={{ color: colors.textMuted, cursor: 'pointer' }}>
            记住我（7 天免登录）
          </label>
        </div>

        {error && (
          <div style={{
            ...errorTextStyle, marginBottom: '1rem', textAlign: 'center',
            padding: '0.5rem', backgroundColor: '#fde8e8', borderRadius: 4,
          }}>
            {error}
          </div>
        )}

        <button type="submit" disabled={isLoading || hasError} style={buttonStyle('primary', isLoading || hasError)}>
          {isLoading ? '登录中…' : '登录'}
        </button>
      </form>
      <p style={{ marginTop: '1.5rem', textAlign: 'center', color: colors.textMuted }}>
        还没有账号？<Link to="/register" style={{ color: colors.primary }}>立即注册</Link>
      </p>
    </div>
  )
}

export default Login
