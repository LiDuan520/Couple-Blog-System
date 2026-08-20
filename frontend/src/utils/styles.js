// 共享样式（无 CSS 框架的临时方案，后续可换 Tailwind）
export const colors = {
  primary: '#007bff',
  primaryHover: '#0056b3',
  success: '#28a745',
  danger: '#dc3545',
  warning: '#ffc107',
  text: '#222',
  textMuted: '#666',
  border: '#ddd',
  bg: '#fafafa',
  bgInput: '#fff',
}

export const buttonStyle = (variant = 'primary', disabled = false) => ({
  width: '100%',
  padding: '0.75rem',
  backgroundColor: disabled ? '#9ec5fe' : colors[variant] || colors.primary,
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  cursor: disabled ? 'not-allowed' : 'pointer',
  fontSize: '1rem',
  fontWeight: 500,
})

export const inputStyle = (hasError = false) => ({
  width: '100%',
  padding: '0.5rem 0.75rem',
  marginTop: '0.25rem',
  border: `1px solid ${hasError ? colors.danger : colors.border}`,
  borderRadius: '4px',
  fontSize: '1rem',
  backgroundColor: colors.bgInput,
  outline: 'none',
})

export const labelStyle = {
  display: 'block',
  fontWeight: 500,
  color: colors.text,
}

export const formGroupStyle = {
  marginBottom: '1rem',
}

export const errorTextStyle = {
  color: colors.danger,
  fontSize: '0.85rem',
  marginTop: '0.25rem',
}
