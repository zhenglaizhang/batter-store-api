# 管理后台使用说明

## 功能概述

管理后台提供了以下功能：
1. **用户注册审核** - 审核用户提交的注册申请
2. **电池订单管理** - 查看和管理电池回收订单

## 访问方式

### 登录页面
访问：`http://your-domain/admin/login`

### 默认管理员账号
- 用户名：`admin`
- 密码：`admin123`

> ⚠️ **安全提示**：生产环境请务必修改默认密码！

## 功能说明

### 1. 用户注册管理 (`/admin/user-review`)

**功能：**
- 查看所有用户注册申请
- 审核用户注册（通过/拒绝）
- 查看用户详细信息（店铺名称、联系人、营业执照等）
- 添加审核备注

**操作流程：**
1. 进入"用户注册管理"页面
2. 查看待审核的用户列表
3. 点击"审核"按钮查看详细信息
4. 选择审核状态（待审核/通过/拒绝）
5. 填写审核备注（可选）
6. 点击"更新状态"完成审核

**状态说明：**
- **待审核** (pending) - 用户已提交，等待审核
- **已通过** (approved) - 审核通过，用户可以正常使用系统
- **已拒绝** (rejected) - 审核未通过

### 2. 电池订单管理 (`/admin/order-tracking`)

**功能：**
- 查看所有电池上传订单
- 查看订单详细信息
- 查看订单中的照片

**操作流程：**
1. 进入"电池订单管理"页面
2. 查看订单列表
3. 点击"查看详情"查看订单详细信息
4. 在详情中查看上传的照片

**订单状态：**
- **待处理** (pending) - 订单已创建，等待处理
- **处理中** (processing) - 订单正在处理中
- **已完成** (completed) - 订单处理完成
- **已取消** (cancelled) - 订单已取消

## 技术实现

### 架构
- **后端**：Flask + SQLAlchemy
- **前端**：HTML + JavaScript + Axios
- **认证**：JWT Token
- **UI**：自定义样式（参考 Ant Design 设计）

### 目录结构
```
wxcloudrun/
├── templates/
│   └── admin/
│       ├── base.html          # 基础模板
│       ├── login.html         # 登录页面
│       ├── dashboard.html     # 仪表板
│       ├── user-review.html   # 用户审核页面
│       └── order-tracking.html # 订单跟踪页面
├── static/
│   └── admin/                 # 静态资源（如需要）
├── middleware.py              # 认证中间件
└── views.py                   # 路由定义
```

### API 端点

管理后台使用的 API 端点：

1. **管理员登录**
   - `POST /api/admin/login`
   - 请求体：`{ "username": "admin", "password": "admin123" }`
   - 返回：`{ "code": 0, "data": { "token": "...", "admin": {...} } }`

2. **获取用户注册列表**
   - `GET /api/user/registrations`
   - 需要认证：Bearer Token

3. **更新用户注册状态**
   - `PUT /api/user/registrations/<registration_id>/status`
   - 请求体：`{ "status": "approved", "review_comment": "..." }`
   - 需要认证：Bearer Token

4. **获取电池订单列表**
   - `GET /api/battery/orders`
   - 需要认证：Bearer Token

5. **获取订单详情**
   - `GET /api/battery/orders/<order_id>`
   - 需要认证：Bearer Token

### 认证机制

1. **登录流程**：
   - 用户在登录页面输入用户名和密码
   - 前端调用 `/api/admin/login` API
   - 成功后，将 token 和管理员信息存储到 `localStorage`
   - 跳转到管理后台首页

2. **Token 使用**：
   - Token 存储在 `localStorage` 中，键名为 `admin_token`
   - 所有 API 请求自动在请求头中添加 `Authorization: Bearer <token>`
   - Token 有效期为 24 小时

3. **退出登录**：
   - 清除 `localStorage` 中的 token 和管理员信息
   - 跳转到登录页面

## 部署说明

### 本地开发
```bash
cd batter-store-api
python3 run.py
```

访问：`http://localhost:80/admin/login`

### 生产部署

1. **修改默认密码**
   - 编辑 `wxcloudrun/handlers/admin_handler.py`
   - 修改 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD`

2. **配置 JWT 密钥**
   - 编辑 `wxcloudrun/handlers/admin_handler.py`
   - 修改 `JWT_SECRET` 为强随机字符串

3. **部署到微信云托管**
   - 按照正常的部署流程部署
   - 管理后台会自动包含在服务中

## 安全建议

1. **修改默认密码**：生产环境必须修改默认管理员密码
2. **使用强 JWT 密钥**：使用足够长的随机字符串作为 JWT 密钥
3. **HTTPS**：生产环境必须使用 HTTPS
4. **IP 白名单**（可选）：限制管理后台的访问 IP
5. **定期更换密码**：建议定期更换管理员密码

## 常见问题

### Q: 登录后提示"未授权"？
A: 检查浏览器控制台，确认 token 是否正确存储。清除浏览器缓存和 localStorage 后重新登录。

### Q: 无法加载用户注册列表？
A: 检查 API 是否正常，确认 token 是否有效。查看浏览器控制台的网络请求。

### Q: 照片无法显示？
A: 检查照片路径是否正确，确认 `/uploads/` 路由是否正常工作。

## 更新日志

### v1.0.0 (2024-01-XX)
- ✅ 实现管理员登录功能
- ✅ 实现用户注册审核功能
- ✅ 实现电池订单管理功能
- ✅ 实现基础认证机制

