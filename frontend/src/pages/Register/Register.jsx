import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { validateInput } from '../../utils/validation'
import {
  colors, buttonStyle, inputStyle, labelStyle, formGroupStyle, errorTextStyle,
} from '../../utils/styles'

function Register() {
  const navigate = useNavigate()
  const { register, isAuthenticated, isLoading, error, clearError } = useAuthStore()
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    nickname: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [touched, setTouched] = useState({})

  useEffect(() => {
    if (isAuthenticated) navigate('/')
  }, [isAuthenticated, navigate])

  useEffect(() => () => clearError(), [clearError])

  const handleChange = (e) => {
    setFormData((p) => ({ ...p, [e.target.name]: e.target.value }))
  }
  const handleBlur = (field) => setTouched((p) => ({ ...p, [field]: true }))

  const errors = {
    username:
      formData.username && !validateInput.username(formData.username)
        ? '3-50 字符，仅字母数字下划线' : '',
    email:
      formData.email && !validateInput.email(formData.email)
        ? '邮箱格式不正确' : '',
    password:
      formData.password && !validateInput.password(formData.password)
        ? '至少 8 位且包含字母+数字' : '',
    confirmPassword:
      formData.confirmPassword && formData.confirmPassword !== formData.password
        ? '两次密码不一致' : '',
  }
  const hasError = Object.values(errors).some(Boolean)
  const strength = validateInput.passwordStrength(formData.password)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setTouched({ username: true, email: true, password: true, confirmPassword: true })
    if (hasError) return
    const { confirmPassword, ...payload } = formData
    // FIX-F-01: 注册成功后自动登录（由 store.register 处理）
    const result = await register(payload)
    if (result.success) navigate('/')
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '420px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '2rem', color: colors.text }}>
        注册
      </h1>
      <form onSubmit={handleSubmit} noValidate>
        <div style={formGroupStyle}>
          <label style={labelStyle}>用户名</label>
          <input
            type="text" name="username" value={formData.username}
            onChange={handleChange} onBlur={() => handleBlur('username')}
            style={inputStyle(touched.username && !!errors.username)}
            autoComplete="username"
          />
          {touched.username && errors.username && <div style={errorTextStyle}>{errors.username}</div>}
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>邮箱</label>
          <input
            type="email" name="email" value={formData.email}
            onChange={handleChange} onBlur={() => handleBlur('email')}
            style={inputStyle(touched.email && !!errors.email)}
            autoComplete="email"
          />
          {touched.email && errors.email && <div style={errorTextStyle}>{errors.email}</div>}
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>密码</label>
          <div style={{ position: 'relative' }}>
            <input
              type={showPassword ? 'text' : 'password'}
              name="password" value={formData.password}
              onChange={handleChange} onBlur={() => handleBlur('password')}
              style={inputStyle(touched.password && !!errors.password)}
              autoComplete="new-password"
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
          {formData.password && (
            <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ flex: 1, height: 4, background: '#eee', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{
                  width: `${(strength + 1) * 25}%`,
                  height: '100%',
                  background: validateInput.passwordStrengthColor(strength),
                  transition: 'width 0.2s',
                }} />
              </div>
              <span style={{ fontSize: 12, color: validateInput.passwordStrengthColor(strength) }}>
                {validateInput.passwordStrengthLabel(strength)}
              </span>
            </div>
          )}
          {touched.password && errors.password && <div style={errorTextStyle}>{errors.password}</div>}
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>确认密码</label>
          <input
            type={showPassword ? 'text' : 'password'}
            name="confirmPassword" value={formData.confirmPassword}
            onChange={handleChange} onBlur={() => handleBlur('confirmPassword')}
            style={inputStyle(touched.confirmPassword && !!errors.confirmPassword)}
            autoComplete="new-password"
          />
          {touched.confirmPassword && errors.confirmPassword && (
            <div style={errorTextStyle}>{errors.confirmPassword}</div>
          )}
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>昵称（可选）</label>
          <input
            type="text" name="nickname" value={formData.nickname}
            onChange={handleChange}
            style={inputStyle(false)}
            maxLength={100}
            placeholder="默认使用用户名"
          />
        </div>

        {error && (
          <div style={{
            ...errorTextStyle, marginBottom: '1rem', textAlign: 'center',
            padding: '0.5rem', backgroundColor: '#fde8e8', borderRadius: 4,
          }}>
            {error}
          </div>
        )}

        <button type="submit" disabled={isLoading || hasError} style={buttonStyle('success', isLoading || hasError)}>
          {isLoading ? '注册中…' : '注册'}
        </button>
      </form>
      <p style={{ marginTop: '1.5rem', textAlign: 'center', color: colors.textMuted }}>
        已有账号？<Link to="/login" style={{ color: colors.primary }}>立即登录</Link>
      </p>
    </div>
  )
}

export default Register
