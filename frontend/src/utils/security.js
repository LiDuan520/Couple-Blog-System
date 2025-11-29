// XSS 防护
export const sanitizeHTML = (str) => {
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

