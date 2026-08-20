import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { userAPI } from '../../api/modules/user.api'
import { validateInput } from '../../utils/validation'
import {
  colors, buttonStyle, inputStyle, labelStyle, formGroupStyle, errorTextStyle,
} from '../../utils/styles'

function Profile() {
  const navigate = useNavigate()
  const { user, logout, changePassword, updateUser } = useAuthStore()
  const [form, setForm] = useState({
    nickname: user?.nickname || '',
    email: user?.email || '',
  })
  const [saving, setSaving] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const fileRef = useRef(null)

  // 修改密码弹窗
  const [showPwdModal, setShowPwdModal] = useState(false)
  const [pwdForm, setPwdForm] = useState({ old_password: '', new_password: '', confirm: '' })
  const [pwdError, setPwdError] = useState('')
  const [pwdSaving, setPwdSaving] = useState(false)

  useEffect(() => {
    if (!user) navigate('/login')
  }, [user, navigate])

  const handleChange = (e) => setForm((p) => ({ ...p, [e.target.name]: e.target.value }))

  const handleSave = async () => {
    setErrorMsg(''); setSuccessMsg('')
    if (form.email && !validateInput.email(form.email)) {
      setErrorMsg('邮箱格式不正确'); return
    }
    setSaving(true)
    try {
      const updated = await userAPI.updateProfile({
        nickname: form.nickname || undefined,
        email: form.email || undefined,
      })
      const data = updated.data || updated
      updateUser(data)
      setSuccessMsg('保存成功')
    } catch (e) {
      setErrorMsg(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setErrorMsg(''); setSuccessMsg('')
    try {
      const res = await userAPI.uploadAvatar(file)
      const data = res.data || res
      // 头像变化后重新拉取用户
      const me = await userAPI.getProfile()
      updateUser(me.data || me)
      setSuccessMsg('头像已更新')
    } catch (e) {
      setErrorMsg(e.message)
    }
  }

  const handleChangePassword = async () => {
    setPwdError('')
    if (!pwdForm.old_password || !pwdForm.new_password) {
      setPwdError('请填写完整'); return
    }
    if (!validateInput.password(pwdForm.new_password)) {
      setPwdError('新密码至少 8 位且包含字母+数字'); return
    }
    if (pwdForm.new_password !== pwdForm.confirm) {
      setPwdError('两次密码不一致'); return
    }
    setPwdSaving(true)
    try {
      const result = await changePassword({
        old_password: pwdForm.old_password,
        new_password: pwdForm.new_password,
      })
      if (result.success) {
        setShowPwdModal(false)
        await logout()
        navigate('/login')
      } else {
        setPwdError(result.error || '修改失败')
      }
    } catch (e) {
      setPwdError(e.message)
    } finally {
      setPwdSaving(false)
    }
  }

  const avatarSrc = userAPI.avatarSrc(user?.avatar)

  return (
    <div style={{ padding: '2rem', maxWidth: 640, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>个人资料</h1>
        <button onClick={() => navigate('/')} style={{ ...buttonStyle('primary', false), width: 'auto', padding: '0.5rem 1rem' }}>
          返回首页
        </button>
      </div>

      <div style={{
        display: 'flex', alignItems: 'center', gap: '1.5rem',
        padding: '1.5rem', background: '#fff', borderRadius: 8,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)', marginBottom: '1.5rem',
      }}>
        <div style={{
          width: 80, height: 80, borderRadius: '50%',
          background: avatarSrc ? `url(${avatarSrc}) center/cover` : colors.primary,
          color: 'white', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: '2rem', fontWeight: 'bold',
        }}>
          {!avatarSrc && (user?.nickname?.[0] || user?.username?.[0] || '?').toUpperCase()}
        </div>
        <div>
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={handleAvatarChange} />
          <button onClick={() => fileRef.current?.click()} style={{ ...buttonStyle('primary', false), width: 'auto' }}>
            更换头像
          </button>
          <p style={{ fontSize: 12, color: colors.textMuted, marginTop: 8 }}>
            支持 jpg/png/gif/webp，最大 2MB
          </p>
        </div>
      </div>

      <div style={{
        padding: '1.5rem', background: '#fff', borderRadius: 8,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
      }}>
        <div style={formGroupStyle}>
          <label style={labelStyle}>用户名（不可改）</label>
          <input value={user?.username || ''} disabled style={{ ...inputStyle(false), background: '#f5f5f5' }} />
        </div>
        <div style={formGroupStyle}>
          <label style={labelStyle}>昵称</label>
          <input name="nickname" value={form.nickname} onChange={handleChange} style={inputStyle(false)} maxLength={100} />
        </div>
        <div style={formGroupStyle}>
          <label style={labelStyle}>邮箱</label>
          <input name="email" type="email" value={form.email} onChange={handleChange} style={inputStyle(false)} />
        </div>

        {errorMsg && <div style={{ ...errorTextStyle, marginBottom: '1rem' }}>{errorMsg}</div>}
        {successMsg && (
          <div style={{ color: colors.success, marginBottom: '1rem' }}>{successMsg}</div>
        )}

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={handleSave} disabled={saving} style={{ ...buttonStyle('success', saving), width: 'auto', flex: 1 }}>
            {saving ? '保存中…' : '保存'}
          </button>
          <button onClick={() => setShowPwdModal(true)} style={{ ...buttonStyle('primary', false), width: 'auto', flex: 1 }}>
            修改密码
          </button>
        </div>
      </div>

      {showPwdModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
        }} onClick={() => setShowPwdModal(false)}>
          <div style={{
            background: '#fff', padding: '2rem', borderRadius: 8, width: 400,
            maxWidth: '90%',
          }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginTop: 0 }}>修改密码</h2>
            <div style={formGroupStyle}>
              <label style={labelStyle}>旧密码</label>
              <input type="password" value={pwdForm.old_password}
                onChange={(e) => setPwdForm((p) => ({ ...p, old_password: e.target.value }))}
                style={inputStyle(false)} />
            </div>
            <div style={formGroupStyle}>
              <label style={labelStyle}>新密码</label>
              <input type="password" value={pwdForm.new_password}
                onChange={(e) => setPwdForm((p) => ({ ...p, new_password: e.target.value }))}
                style={inputStyle(false)} />
            </div>
            <div style={formGroupStyle}>
              <label style={labelStyle}>确认新密码</label>
              <input type="password" value={pwdForm.confirm}
                onChange={(e) => setPwdForm((p) => ({ ...p, confirm: e.target.value }))}
                style={inputStyle(false)} />
            </div>
            {pwdError && <div style={{ ...errorTextStyle, marginBottom: '1rem' }}>{pwdError}</div>}
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={() => setShowPwdModal(false)} style={{ ...buttonStyle('primary', false), width: 'auto', flex: 1, background: '#6c757d' }}>
                取消
              </button>
              <button onClick={handleChangePassword} disabled={pwdSaving} style={{ ...buttonStyle('success', pwdSaving), width: 'auto', flex: 1 }}>
                {pwdSaving ? '提交中…' : '确认'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Profile
