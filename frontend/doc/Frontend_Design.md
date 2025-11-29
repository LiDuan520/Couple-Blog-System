# 情侣博客系统 - 前端设计文档

## 文档信息
- **文档版本**: v1.0.0
- **创建日期**: 2024-01-XX
- **最后更新**: 2024-01-XX
- **文档作者**: 技术团队
- **审核状态**: 待审核

---

## 目录
1. [项目结构](#1-项目结构)
2. [技术架构](#2-技术架构)
3. [状态管理设计](#3-状态管理设计)
4. [组件设计](#4-组件设计)
5. [路由设计](#5-路由设计)
6. [性能优化](#6-性能优化)
7. [安全设计](#7-安全设计)

---

## 1. 项目结构

```
frontend/
├── public/
├── src/
│   ├── main.jsx                # 应用入口
│   ├── App.jsx                 # 根组件
│   │
│   ├── api/                    # API 客户端
│   │   ├── client.js           # Axios 配置
│   │   ├── endpoints.js        # API 端点常量
│   │   └── modules/            # 模块化 API
│   │       ├── auth.api.js
│   │       ├── blog.api.js
│   │       └── user.api.js
│   │
│   ├── store/                  # 状态管理（Zustand）
│   │   ├── index.js
│   │   ├── authStore.js
│   │   ├── blogStore.js
│   │   └── userStore.js
│   │
│   ├── hooks/                  # 自定义 Hooks
│   │   ├── useAuth.js
│   │   ├── useBlog.js
│   │   ├── useQuery.js         # React Query 封装
│   │   └── useCleanup.js       # 清理 Hook
│   │
│   ├── services/               # 业务服务层
│   │   ├── authService.js
│   │   ├── blogService.js
│   │   └── cacheService.js
│   │
│   ├── components/             # 组件
│   │   ├── common/             # 通用组件
│   │   │   ├── Button/
│   │   │   ├── Input/
│   │   │   ├── Modal/
│   │   │   └── Loading/
│   │   ├── layout/             # 布局组件
│   │   │   ├── Header/
│   │   │   ├── Sidebar/
│   │   │   └── Footer/
│   │   └── features/           # 功能组件
│   │       ├── auth/
│   │       │   ├── LoginForm/
│   │       │   └── RegisterForm/
│   │       └── blog/
│   │           ├── BlogList/
│   │           ├── BlogCard/
│   │           └── BlogEditor/
│   │
│   ├── pages/                  # 页面
│   │   ├── Login/
│   │   ├── Register/
│   │   ├── Dashboard/
│   │   ├── BlogList/
│   │   ├── BlogDetail/
│   │   └── BlogEdit/
│   │
│   ├── utils/                  # 工具函数
│   │   ├── validation.js       # 前端验证
│   │   ├── security.js         # 安全工具
│   │   ├── storage.js          # 本地存储
│   │   └── errorHandler.js     # 错误处理
│   │
│   ├── constants/              # 常量
│   │   └── index.js
│   │
│   └── styles/                 # 样式
│       ├── global.css
│       └── variables.css
│
├── package.json
└── vite.config.js
```

---

## 2. 技术架构

### 2.1 技术栈

- **框架**: React 18+
- **构建工具**: Vite 5+
- **状态管理**: Zustand 4+
- **数据获取**: React Query 5+
- **路由**: React Router 6+
- **HTTP 客户端**: Axios 1.6+

### 2.2 架构图

```
┌─────────────────────────────────────┐
│          React 应用层                │
│  ┌──────────┐  ┌──────────┐        │
│  │  Pages   │  │Components│        │
│  └────┬─────┘  └────┬─────┘        │
│       │             │               │
│  ┌────▼─────────────▼─────┐        │
│  │    Custom Hooks         │        │
│  │  (useAuth, useBlog)     │        │
│  └────┬────────────────────┘        │
│       │                             │
│  ┌────▼─────────────┬───────────┐  │
│  │  Zustand Store   │React Query│  │
│  └────┬─────────────┴─────┬─────┘  │
│       │                   │         │
│  ┌────▼───────────────────▼─────┐  │
│  │      API Client (Axios)       │  │
│  └───────────────┬───────────────┘  │
└──────────────────┼──────────────────┘
                   │
          ┌─────────▼─────────┐
          │   Backend API     │
          └───────────────────┘
```

---

## 3. 状态管理设计

### 3.1 Zustand Store 结构

#### 3.1.1 authStore

```javascript
{
  // 状态
  user: User | null,
  token: string | null,
  isAuthenticated: boolean,
  isLoading: boolean,
  error: string | null,
  
  // 方法
  login: (credentials) => Promise,
  register: (userData) => Promise,
  logout: () => Promise,
  init: () => Promise,
  clearError: () => void
}
```

#### 3.1.2 blogStore

```javascript
{
  // 状态
  blogs: Blog[],
  currentBlog: Blog | null,
  filters: FilterOptions,
  isLoading: boolean,
  error: string | null,
  
  // 方法
  fetchBlogs: (filters) => Promise,
  fetchBlog: (id) => Promise,
  createBlog: (data) => Promise,
  updateBlog: (id, data) => Promise,
  deleteBlog: (id) => Promise
}
```

### 3.2 React Query 缓存策略

#### 3.2.1 查询键设计

```javascript
// 扁平化查询键
['blogs']                    // 所有博客相关
['blogs', 'list']            // 博客列表
['blogs', 'list', filters]   // 带筛选的列表
['blogs', 'detail', id]      // 博客详情
```

#### 3.2.2 缓存配置

```javascript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5分钟
      cacheTime: 10 * 60 * 1000,      // 10分钟
      retry: 2,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
  },
});
```

---

## 4. 组件设计

### 4.1 组件分类

- **页面组件** (Pages): 路由对应的页面
- **功能组件** (Features): 业务功能组件
- **通用组件** (Common): 可复用 UI 组件
- **布局组件** (Layout): 页面布局组件

### 4.2 组件规范

- 使用函数组件 + Hooks
- Props 类型检查（PropTypes）
- 使用 `memo` 优化性能
- 事件处理使用 `useCallback`
- 副作用使用 `useEffect`，注意清理

### 4.3 组件示例

```javascript
// components/common/Button/Button.jsx
import { memo, useCallback } from 'react';
import PropTypes from 'prop-types';

const Button = memo(({ 
  children, 
  onClick, 
  variant = 'primary', 
  disabled = false,
  ...props 
}) => {
  const handleClick = useCallback((e) => {
    if (!disabled && onClick) {
      onClick(e);
    }
  }, [disabled, onClick]);
  
  return (
    <button
      className={`btn btn-${variant}`}
      onClick={handleClick}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
});

Button.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger']),
  disabled: PropTypes.bool,
};

export default Button;
```

---

## 5. 路由设计

### 5.1 路由配置

```javascript
/                    → 首页（重定向到 Dashboard）
/login               → 登录页
/register            → 注册页
/dashboard           → 仪表盘（博客列表）
/blogs               → 博客列表
/blogs/:id           → 博客详情
/blogs/:id/edit      → 编辑博客
/blogs/new           → 创建博客
/profile             → 个人资料
```

### 5.2 路由守卫

```javascript
// 保护需要认证的路由
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  return children;
};
```

---

## 6. 性能优化

### 6.1 代码分割

```javascript
// 路由懒加载
const BlogList = lazy(() => import('./pages/BlogList'));
const BlogDetail = lazy(() => import('./pages/BlogDetail'));

// 使用 Suspense
<Suspense fallback={<Loading />}>
  <Routes>
    <Route path="/blogs" element={<BlogList />} />
  </Routes>
</Suspense>
```

### 6.2 缓存策略

- React Query 自动缓存
- 本地存储缓存（Zustand persist）
- HTTP 缓存头（未来功能）

### 6.3 内存管理

- 请求取消（AbortController）
- 事件监听器清理
- 定时器清理
- 组件卸载时清理副作用

```javascript
// hooks/useCleanup.js
export const useCleanup = (cleanupFn) => {
  useEffect(() => {
    return () => {
      if (cleanupFn) cleanupFn();
    };
  }, [cleanupFn]);
};
```

---

## 7. 安全设计

### 7.1 输入验证

```javascript
// utils/validation.js
export const validateInput = {
  email: (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  },
  
  password: (password) => {
    return password.length >= 8 && 
           /[A-Za-z]/.test(password) && 
           /[0-9]/.test(password);
  },
};
```

### 7.2 XSS 防护

```javascript
// utils/security.js
export const sanitizeHTML = (str) => {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
};
```

### 7.3 Token 管理

```javascript
// utils/storage.js
export const setToken = (token) => {
  localStorage.setItem('token', token);
};

export const getToken = () => {
  return localStorage.getItem('token');
};

export const removeToken = () => {
  localStorage.removeItem('token');
};
```

---

## 8. 开发规范

### 8.1 代码规范
- ESLint + Prettier
- 函数组件优先
- Hooks 规则遵守

### 8.2 命名规范
- 组件：PascalCase（如 `BlogCard`）
- 函数/变量：camelCase（如 `getBlogList`）
- 常量：UPPER_SNAKE_CASE（如 `API_BASE_URL`）
- 文件：与组件/功能同名

### 8.3 Git 规范
- Conventional Commits
- 功能分支开发
- PR 代码审查

---

## 9. 测试策略

### 9.1 单元测试
- 组件测试（React Testing Library）
- Hook 测试
- 工具函数测试

### 9.2 集成测试
- 页面流程测试
- API 集成测试

---

## 10. 部署方案

### 10.1 构建

```bash
npm run build
```

### 10.2 部署
- 静态文件部署到 Nginx/CDN
- 环境变量配置
- 生产环境优化

---

**文档状态**: ✅ 已完成
**下一步**: 开始前端开发

