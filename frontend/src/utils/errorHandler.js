// 统一错误处理
export const errorHandler = (error) => {
  if (error.response) {
    // 服务器响应错误
    const { status, data } = error.response
    
    switch (status) {
      case 400:
        return data?.error?.message || '请求参数错误'
      case 401:
        return '未授权，请重新登录'
      case 403:
        return '没有权限访问'
      case 404:
        return '资源未找到'
      case 422:
        return data?.error?.message || '数据验证失败'
      case 500:
        return '服务器内部错误'
      default:
        return data?.error?.message || '请求失败'
    }
  } else if (error.request) {
    // 请求发送但无响应
    return '网络错误，请检查网络连接'
  } else {
    // 其他错误
    return error.message || '未知错误'
  }
}

