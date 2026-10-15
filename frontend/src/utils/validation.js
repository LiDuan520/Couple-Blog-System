// 表单校验工具
export const validateInput = {
  email: (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email || ''),

  password: (password) =>
    (password || '').length >= 8 &&
    /[A-Za-z]/.test(password) &&
    /[0-9]/.test(password),

  username: (username) => /^[a-zA-Z0-9_]{3,50}$/.test(username || ''),

  // 密码强度：0-3
  passwordStrength: (password) => {
    if (!password) return 0
    let score = 0
    if (password.length >= 8) score++
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++
    if (/[0-9]/.test(password)) score++
    if (/[^A-Za-z0-9]/.test(password)) score++
    return Math.min(score, 3)
  },

  passwordStrengthLabel: (score) =>
    ['弱', '中', '强', '很强'][score] || '弱',

  passwordStrengthColor: (score) =>
    ['#dc3545', '#fd7e14', '#28a745', '#198754'][score] || '#dc3545',
}
