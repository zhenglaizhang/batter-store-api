# 微信云托管对象存储配置说明

## 概述

`/api/upload/photos` 接口已改为使用微信云托管对象存储服务来存储上传的照片文件。使用 requests 调用微信云托管 API 获取临时密钥和文件元数据，然后使用腾讯云 COS Python SDK 进行文件上传和下载。

参考文档：[微信云托管 COS-SDK 服务端使用](https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloudrun/src/development/storage/service/cos-sdk.html)

## 环境变量配置

在 `.env` 文件中需要配置以下环境变量以连接微信云托管对象存储服务：

### 必需配置

```env
# COS 存储桶所在地域
COS_REGION=ap-shanghai

# COS 存储桶名称
COS_BUCKET_NAME=your_bucket_name_here
```

**注意**：不需要配置 SecretId 和 SecretKey，系统会自动通过微信云托管 API 获取临时密钥。

## 配置获取方式

### 1. 获取存储桶名称和地域

1. 登录 [微信云托管控制台](https://console.cloud.tencent.com/tcb)
2. 进入 **对象存储** -> **存储配置**
3. 查看或配置存储桶信息：
   - **存储桶名称**（Bucket Name）
   - **所属地域**（Region），默认是上海（ap-shanghai）

### 3. 地域代码对照

常用地域代码：
- `ap-beijing` - 北京
- `ap-shanghai` - 上海
- `ap-guangzhou` - 广州
- `ap-chengdu` - 成都
- `ap-chongqing` - 重庆
- `ap-singapore` - 新加坡

完整列表：https://cloud.tencent.com/document/product/436/6224

## 工作原理

1. **获取临时密钥**: 通过 `http://api.weixin.qq.com/_/cos/getauth` 获取临时密钥（自动缓存，提前5分钟刷新）
2. **初始化 COS 客户端**: 使用临时密钥初始化腾讯云 COS SDK 客户端
3. **获取文件元数据**: 上传前通过 `https://api.weixin.qq.com/_/cos/metaid/encode` 获取文件元数据（确保小程序端可以访问）
4. **上传文件**: 使用 `put_object` 方法上传文件，并在 Headers 中添加 `x-cos-meta-fileid` 元数据
5. **存储 COS Key**: 上传成功后，将 COS 文件路径（Key，格式：`photos/{user_id}/{filename}`）存储到数据库中（存储在 `file_path` 字段）
6. **生成下载URL**: 使用 `get_presigned_download_url` 方法生成预签名下载URL（有效期可配置）

**重要**：文件元数据是必需的，没有元数据的文件小程序端无法访问！

## API 响应变化

上传成功后，API 响应中会包含以下新字段：

```json
{
  "photos": [
    {
      "id": "photo_id",
      "filename": "unique_filename.jpg",
      "original_filename": "original.jpg",
      "cos_key": "photos/user_xxx/uuid.jpg",  // COS 文件路径（Key）
      "file_path": "photos/user_xxx/uuid.jpg",  // 兼容字段，实际存储的是COS Key
      "download_url": "https://...",  // 预签名下载URL（临时有效）
      "file_size": 12345,
      "mime_type": "image/jpeg",
      "upload_index": 0,
      "created_at": "2025-11-15T10:00:00Z"
    }
  ]
}
```

## 注意事项

1. **文件大小限制**: 单个文件最大 10MB
2. **支持的文件类型**: jpg, jpeg, png, gif, webp
3. **下载URL有效期**: 通过 `get_file_download_url` 获取的预签名下载URL默认有效期为 1 小时（3600秒），可在调用时自定义
4. **数据库存储**: `file_path` 字段现在存储的是 COS 文件路径（Key），格式：`photos/{user_id}/{filename}`
5. **向后兼容**: 代码会检查 `file_path` 是否以 `photos/` 开头来判断是 COS Key 还是本地路径
6. **存储桶权限**: 确保存储桶的访问权限配置正确，建议使用私有读写权限，通过预签名URL访问

## 错误处理

如果上传失败，可能的原因：

1. **配置错误**: 检查 `.env` 文件中的 `COS_REGION`、`COS_BUCKET_NAME` 是否正确
2. **环境问题**: 确认服务运行在微信云托管环境中（临时密钥 API 只在云托管环境可用）
3. **网络问题**: 检查服务器是否能访问微信云托管 API 和腾讯云 COS 服务
4. **存储桶不存在**: 确认 `COS_BUCKET_NAME` 与微信云托管控制台中的存储桶名称一致
5. **地域不匹配**: 确认 `COS_REGION` 与存储桶所属地域一致
6. **元数据获取失败**: 如果无法获取文件元数据，文件上传后小程序端将无法访问

## 额外功能

除了上传和下载，还提供了以下功能：

- **删除文件**: `delete_file_from_cos(cos_key)` - 从 COS 删除指定文件
- **下载到本地**: `download_file_from_cos(cos_key, local_path)` - 将 COS 文件下载到本地路径
- **解析元数据**: `decode_file_metadata(metaid)` - 解析文件元数据，获取 openid、bucket、path 等信息

## 使用限制

1. **服务环境**: 必须在微信云托管环境中运行才能使用临时密钥 API
2. **文件元数据**: 文件缺少元数据时，小程序端无法访问，请务必确保上传时获取并写入元数据
3. **请求体大小**: 云托管域名请求体大小二进制限制 20MiB，超大文件请从客户端上传
4. **临时密钥缓存**: 临时密钥会自动缓存，提前5分钟刷新，无需手动管理

## 测试

可以使用以下方式测试上传功能：

```bash
curl -X POST http://localhost:3000/api/upload/photos \
  -F "user_id=your_user_id" \
  -F "photos_0=@test_image.jpg"
```

确保：
1. 用户ID对应的用户已注册且状态为 `approved`
2. 测试图片文件大小不超过 10MB
3. 图片格式为支持的格式之一

