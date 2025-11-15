# Battery Recycling API - Python Flask 迁移说明

本项目已从 Rust (Axum) 迁移到 Python (Flask)，所有 API 功能已完整迁移。

## 项目结构

```
batter-store-api/
├── wxcloudrun/
│   ├── __init__.py          # Flask 应用初始化
│   ├── models.py            # 数据模型（SQLAlchemy）
│   ├── dao.py               # 数据访问层
│   ├── views.py             # 路由定义
│   ├── response.py          # 响应工具函数
│   ├── utils.py             # 工具函数
│   ├── handlers/            # API 处理器
│   │   ├── user_handler.py      # 用户相关 API
│   │   ├── upload_handler.py    # 上传相关 API
│   │   └── admin_handler.py     # 管理员相关 API
│   └── model.py             # 原有计数器模型（保留）
├── migrations/              # 数据库迁移脚本
│   ├── 001_initial_schema.sql
│   ├── 002_battery_upload_orders.sql
│   └── 003_add_business_license.sql
├── docker-compose.yml       # Docker Compose 配置
├── Dockerfile               # Docker 镜像配置
├── requirements.txt         # Python 依赖
└── run.py                   # 应用启动入口

```

## API 端点

所有 API 端点与 Rust 版本保持一致：

### 用户相关
- `POST /api/user/register` - 用户注册
- `GET /api/user/profile` - 获取用户个人信息
- `GET /api/user/registrations` - 获取所有用户注册记录（管理员）
- `PUT /api/user/registrations/<registration_id>/status` - 更新用户注册状态（管理员）

### 上传相关
- `POST /api/upload/photos` - 上传照片
- `GET /api/upload/photos` - 获取上传的照片列表
- `POST /api/upload/business-license` - 上传营业执照

### 电池订单相关
- `GET /api/battery/orders` - 获取所有电池上传订单（管理员）
- `POST /api/battery/orders` - 创建电池订单
- `GET /api/battery/orders/<order_id>` - 获取电池上传订单详情（管理员）

### 管理员相关
- `POST /api/admin/login` - 管理员登录

## 环境变量配置

创建 `.env` 文件或设置以下环境变量：

```bash
# 数据库配置
DATABASE_URL=mysql://battery_user:password@localhost:3306/battery_recycling
MYSQL_USERNAME=battery_user
MYSQL_PASSWORD=password
MYSQL_ADDRESS=localhost:3306
MYSQL_DATABASE=battery_recycling

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=3000

# 其他配置
DEBUG=True
LOG_LEVEL=info
```

## 使用 Docker Compose 启动

1. 启动所有服务（包括 MySQL 8）：
```bash
cd batter-store-api
docker-compose up -d
```

2. 查看日志：
```bash
docker-compose logs -f app
```

3. 停止服务：
```bash
docker-compose down
```

## 本地开发

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 确保 MySQL 8 正在运行，并已创建数据库

3. 运行迁移脚本（如果需要）：
```bash
mysql -u battery_user -p battery_recycling < migrations/001_initial_schema.sql
mysql -u battery_user -p battery_recycling < migrations/002_battery_upload_orders.sql
mysql -u battery_user -p battery_recycling < migrations/003_add_business_license.sql
```

4. 启动应用：
```bash
python run.py
```

## 数据库

- 使用 MySQL 8.0
- 数据库迁移脚本位于 `migrations/` 目录
- SQLAlchemy 会自动创建表（如果不存在）

## 主要变更

1. **响应格式**：统一使用 `ApiResponse` 格式，与 Rust 版本保持一致
2. **错误处理**：使用统一的错误响应格式
3. **文件上传**：支持多文件上传和营业执照上传
4. **数据库**：使用 SQLAlchemy ORM，支持自动迁移

## 注意事项

- 上传的文件存储在 `uploads/` 目录
- 确保 `uploads/` 目录有写入权限
- 管理员登录凭据：用户名 `admin`，密码 `admin123`
- JWT token 有效期为 24 小时

