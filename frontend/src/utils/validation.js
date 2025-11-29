// 输入验证
export const validateInput = {
  email: (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return re.test(email)
  },
  
  password: (password) => {
    return password.length >= 8 && 
           /[A-Za-z]/.test(password) && 
           /[0-9]/.test(password)
  },
  
  username: (username) => {
    return /^[a-zA-Z0-9_]{3,50}$/.test(username)
  },
}

