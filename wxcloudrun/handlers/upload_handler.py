import logging
import os
import uuid
import json
from datetime import datetime
from flask import request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from wxcloudrun import db
from wxcloudrun.models import BatteryUploadPhoto
from wxcloudrun.dao import (
    get_user_registration_by_user_id, create_battery_upload_order,
    get_all_battery_upload_orders, get_battery_upload_order_by_id,
    create_battery_upload_photo, get_photos_by_order_id,
    update_user_business_license_path
)
from wxcloudrun.utils import is_valid_image_type, get_mime_type
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.cos_storage import upload_photo_to_cos, get_file_download_url, extract_cos_key_from_file_path

logger = logging.getLogger('log')


def upload_photos():
    """
    上传照片接口
    """
    try:
        logger.info("开始处理照片上传请求")
        
        # 检查是否有文件
        if 'user_id' not in request.form:
            return make_err_response("缺少user_id参数"), 400
        
        user_id = request.form['user_id']
        
        # 验证用户是否存在且已审核通过
        user = get_user_registration_by_user_id(user_id)
        if user is None or user.status != 'approved':
            logger.error("用户不存在或未审核通过: %s", user_id)
            return make_err_response("用户不存在或未审核通过"), 400
        
        logger.info("找到用户信息: %s - %s", user.store_name, user.contact_name)
        
        # 收集上传的文件
        uploaded_files = []
        file_index = 0
        
        # 处理所有以 photos_ 开头的文件字段
        for key in request.files:
            if key.startswith('photos_'):
                file = request.files[key]
                if file and file.filename:
                    filename = file.filename
                    
                    # 验证文件类型
                    if not is_valid_image_type(filename):
                        logger.warn("不支持的文件类型: %s", filename)
                        continue
                    
                    # 获取上传索引
                    try:
                        upload_index = int(key.replace('photos_', ''))
                    except:
                        upload_index = file_index
                        file_index += 1
                    
                    # 读取文件数据
                    file_data = file.read()
                    
                    # 验证文件大小 (限制为10MB)
                    if len(file_data) > 10 * 1024 * 1024:
                        logger.warn("文件过大: %d bytes", len(file_data))
                        continue
                    
                    uploaded_files.append((filename, file_data, upload_index))
        
        if not uploaded_files:
            return make_err_response("没有有效的照片文件"), 400
        
        # 开始数据库事务
        try:
            # 创建电池上传订单
            order_id = str(uuid.uuid4())
            order_data = {
                'id': order_id,
                'user_id': user_id,
                'store_name': user.store_name,
                'contact_name': user.contact_name,
                'contact_phone': user.contact_phone,
                'contact_address': user.address,
                'total_photos': len(uploaded_files),
                'status': 'pending',
            }
            order = create_battery_upload_order(order_data)
            
            # 上传照片到微信云托管对象存储并插入数据库记录
            photos = []
            for original_filename, file_data, upload_index in uploaded_files:
                # 生成唯一文件名
                file_extension = os.path.splitext(original_filename)[1][1:] or 'jpg'
                unique_filename = f"{uuid.uuid4()}.{file_extension}"
                
                # 上传到微信云托管对象存储
                # openid 为空字符串表示管理端上传，小程序端需要传入实际 openid
                openid = request.form.get('openid', '')
                cos_key = upload_photo_to_cos(file_data, user_id, unique_filename, openid=openid)
                
                # 如果 COS 上传失败，回退到本地存储（用于本地开发环境）
                if not cos_key:
                    logger.warning("COS 上传失败，回退到本地存储: %s", original_filename)
                    # 创建用户专用上传目录
                    user_upload_dir = os.path.join('uploads', 'photos', user_id)
                    os.makedirs(user_upload_dir, exist_ok=True)
                    
                    # 保存到本地
                    local_file_path = os.path.join(user_upload_dir, unique_filename)
                    with open(local_file_path, 'wb') as f:
                        f.write(file_data)
                    
                    # 使用本地路径作为 file_path
                    cos_key = local_file_path
                    logger.info("文件已保存到本地: %s", local_file_path)
                
                # 获取MIME类型
                mime_type = get_mime_type(file_extension)
                
                # 插入照片记录到数据库（file_path 存储 COS Key）
                photo_data = {
                    'id': str(uuid.uuid4()),
                    'order_id': order_id,
                    'user_id': user_id,
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'file_path': cos_key,  # 存储 COS 文件路径（Key）
                    'file_size': len(file_data),
                    'mime_type': mime_type,
                    'upload_index': upload_index,
                }
                photo = create_battery_upload_photo(photo_data)
                
                # 获取下载URL
                # 如果是 COS Key（以 photos/ 开头且不是绝对路径），获取预签名URL
                # 否则是本地文件路径，生成相对URL
                if cos_key.startswith('photos/') and not os.path.isabs(cos_key):
                    download_url = get_file_download_url(cos_key, expires=3600)
                else:
                    # 本地文件，生成相对URL
                    rel_path = os.path.relpath(cos_key, 'uploads')
                    download_url = f"/uploads/{rel_path}"
                
                # 判断是 COS Key 还是本地路径
                is_cos_key = cos_key.startswith('photos/') and not os.path.isabs(cos_key)
                
                photos.append({
                    'id': photo.id,
                    'filename': photo.filename,
                    'original_filename': photo.original_filename,
                    'cos_key': cos_key if is_cos_key else None,  # COS 文件路径（Key），本地文件时为 None
                    'file_path': photo.file_path,  # 存储路径（COS Key 或本地路径）
                    'download_url': download_url,  # 预签名下载URL 或本地文件URL
                    'file_size': photo.file_size,
                    'mime_type': photo.mime_type,
                    'upload_index': photo.upload_index,
                    'created_at': photo.created_at.isoformat() + 'Z' if photo.created_at else None,
                })
                
                if is_cos_key:
                    logger.info("文件上传成功到 COS: %s, cos_key: %s", unique_filename, cos_key)
                else:
                    logger.info("文件保存到本地: %s, file_path: %s", unique_filename, cos_key)
            
            logger.info("照片上传完成，共上传 %d 个文件，订单ID: %s", len(photos), order_id)
            
            # 构建响应
            response_data = {
                'order_id': order.id,
                'user_id': order.user_id,
                'store_name': order.store_name,
                'contact_name': order.contact_name,
                'contact_phone': order.contact_phone,
                'contact_address': order.contact_address,
                'status': order.status,
                'total_photos': order.total_photos,
                'photos': photos,
                'created_at': order.created_at.isoformat() + 'Z' if order.created_at else None,
            }
            
            return make_succ_response(response_data), 200
            
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error("❌ 照片上传失败: %s", str(e), exc_info=True)
        return make_err_response(f"照片上传失败: {str(e)}"), 500


def upload_business_license():
    """
    上传营业执照照片
    """
    try:
        logger.info("开始处理营业执照上传请求")
        
        # 检查是否有文件
        if 'user_id' not in request.form:
            return make_err_response("缺少user_id参数"), 400
        
        if 'business_license' not in request.files:
            return make_err_response("没有找到营业执照文件"), 400
        
        user_id = request.form['user_id']
        file = request.files['business_license']
        
        if not file or not file.filename:
            return make_err_response("没有找到营业执照文件"), 400
        
        filename = file.filename
        logger.info("处理营业执照上传: %s", filename)
        
        # 验证文件类型
        if not is_valid_image_type(filename):
            logger.warn("不支持的文件类型: %s", filename)
            return make_err_response("不支持的文件类型，请上传图片文件"), 400
        
        # 读取文件数据
        file_data = file.read()
        
        # 验证文件大小 (限制为5MB)
        if len(file_data) > 5 * 1024 * 1024:
            logger.warn("文件过大: %d bytes", len(file_data))
            return make_err_response("文件过大，请上传小于5MB的图片"), 400
        
        # 创建用户专用上传目录
        user_upload_dir = os.path.join('uploads', 'business_licenses', user_id)
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # 生成唯一文件名
        file_extension = os.path.splitext(filename)[1][1:] or 'jpg'
        unique_filename = f"business_license_{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(user_upload_dir, unique_filename)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # 更新用户注册记录中的营业执照路径
        success = update_user_business_license_path(user_id, file_path)
        if not success:
            return make_err_response("更新营业执照路径失败"), 500
        
        logger.info("营业执照上传成功: %s", unique_filename)
        
        response_data = {
            'success': True,
            'message': '营业执照上传成功',
            'data': {
                'url': file_path,
                'filename': unique_filename,
                'size': len(file_data),
            }
        }
        
        return make_succ_response(response_data, "营业执照上传成功"), 200
        
    except Exception as e:
        logger.error("❌ 营业执照上传失败: %s", str(e), exc_info=True)
        return make_err_response(f"营业执照上传失败: {str(e)}"), 500


def get_uploaded_photos():
    """
    获取上传的照片列表
    """
    try:
        upload_dir = os.path.join('uploads', 'photos')
        
        if not os.path.exists(upload_dir):
            return make_succ_response([]), 200
        
        files = []
        for root, dirs, filenames in os.walk(upload_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_stat = os.stat(file_path)
                
                # 计算相对路径
                rel_path = os.path.relpath(file_path, 'uploads')
                
                files.append({
                    'filename': filename,
                    'url': f"/uploads/{rel_path}",
                    'size': file_stat.st_size,
                    'created_at': datetime.fromtimestamp(file_stat.st_ctime).isoformat() + 'Z',
                })
        
        return make_succ_response(files, "获取照片列表成功"), 200
        
    except Exception as e:
        logger.error("❌ 获取照片列表失败: %s", str(e), exc_info=True)
        return make_err_response(f"获取照片列表失败: {str(e)}"), 500


def get_all_battery_orders():
    """
    获取所有电池上传订单（管理员功能）
    """
    try:
        # ========== 请求日志 ==========
        logger.info("=" * 80)
        logger.info("📥 [REQUEST] GET /api/battery/orders")
        logger.info("📋 请求参数:")
        logger.info("   request.method: %s", request.method)
        logger.info("   request.url: %s", request.url)
        logger.info("   request.args: %s", dict(request.args))
        logger.info("=" * 80)
        
        orders = get_all_battery_upload_orders()
        logger.info("📦 从数据库获取到 %d 个订单", len(orders))
        
        order_responses = []
        for order in orders:
            # 获取每个订单的照片
            photos = get_photos_by_order_id(order.id)
            
            photo_responses = []
            for photo in photos:
                # 只返回云存储相对路径，不返回下载URL
                # 小程序端会使用 wx.cloud.getTempFileURL 来获取临时访问URL
                photo_responses.append({
                    'id': photo.id,
                    'filename': photo.filename,
                    'original_filename': photo.original_filename,
                    'file_path': photo.file_path,  # 云存储相对路径，如 'photos/user_id/timestamp.jpg'
                    'file_size': photo.file_size,
                    'mime_type': photo.mime_type,
                    'upload_index': photo.upload_index,
                    'created_at': photo.created_at.isoformat() + 'Z' if photo.created_at else None,
                })
            
            order_data = {
                'order_id': order.id,
                'user_id': order.user_id,
                'store_name': order.store_name,
                'contact_name': order.contact_name,
                'contact_phone': order.contact_phone,
                'contact_address': order.contact_address,
                'status': order.status,
                'total_photos': order.total_photos,
                'photos': photo_responses,
                'created_at': order.created_at.isoformat() + 'Z' if order.created_at else None,
            }
            order_responses.append(order_data)
            
            # 打印每个订单的关键信息
            logger.info("   订单 #%d: order_id=%s, created_at=%s, total_photos=%d, photos数量=%d", 
                       len(order_responses), order.id, order_data['created_at'], order.total_photos, len(photo_responses))
        
        # ========== 响应日志 ==========
        logger.info("=" * 80)
        logger.info("📤 [RESPONSE] GET /api/battery/orders")
        logger.info("   状态码: 200")
        logger.info("   订单总数: %d", len(order_responses))
        logger.info("   前3个订单的 created_at:")
        for i, order in enumerate(order_responses[:3]):
            logger.info("     订单 %d: order_id=%s, created_at=%s", i+1, order['order_id'], order['created_at'])
        logger.info("=" * 80)
        
        return make_succ_response(order_responses, "获取电池上传订单成功"), 200
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ [ERROR] GET /api/battery/orders")
        logger.error("   错误信息: %s", str(e))
        logger.error("=" * 80)
        logger.error("❌ 获取电池订单失败: %s", str(e), exc_info=True)
        return make_err_response(f"获取电池订单失败: {str(e)}"), 500


def get_battery_order_detail(order_id):
    """
    获取电池上传订单详情（管理员功能）
    """
    try:
        # ========== 请求日志 ==========
        logger.info("=" * 80)
        logger.info("📥 [REQUEST] GET /api/battery/orders/<order_id>")
        logger.info("📋 请求参数:")
        logger.info("   order_id: %s", order_id)
        logger.info("   request.method: %s", request.method)
        logger.info("   request.url: %s", request.url)
        logger.info("   request.args: %s", dict(request.args))
        logger.info("=" * 80)
        
        order = get_battery_upload_order_by_id(order_id)
        if order is None:
            logger.warn("⚠️ 未找到指定的电池订单: %s", order_id)
            logger.info("=" * 80)
            logger.info("📤 [RESPONSE] GET /api/battery/orders/<order_id>")
            logger.info("   状态码: 404")
            logger.info("   响应: 未找到指定的电池订单")
            logger.info("=" * 80)
            return make_err_response("未找到指定的电池订单"), 404
        
        # 打印订单基本信息
        logger.info("📦 订单基本信息:")
        logger.info("   order.id: %s", order.id)
        logger.info("   order.user_id: %s", order.user_id)
        logger.info("   order.store_name: %s", order.store_name)
        logger.info("   order.status: %s", order.status)
        logger.info("   order.total_photos: %s", order.total_photos)
        logger.info("   order.created_at: %s", order.created_at)
        logger.info("   order.created_at (ISO格式): %s", order.created_at.isoformat() + 'Z' if order.created_at else None)
        
        # 获取订单照片
        photos = get_photos_by_order_id(order_id)
        logger.info("📸 订单照片信息:")
        logger.info("   照片数量: %d", len(photos))
        
        photo_responses = []
        for index, photo in enumerate(photos):
            # 生成预签名下载URL（有效期1小时）
            download_url = None
            if photo.file_path:
                # 从 file_path 中提取 COS Key（支持 cloud:// 格式和 photos/ 格式）
                cos_key = extract_cos_key_from_file_path(photo.file_path)
                
                if cos_key:
                    # 成功提取 COS Key，生成预签名URL
                    download_url = get_file_download_url(cos_key, expires=3600)
                    logger.info("   照片 #%d 预签名URL: %s (从 %s 提取)", index + 1, download_url, photo.file_path)
                else:
                    # 无法提取 COS Key，可能是本地文件，生成相对URL
                    if 'uploads' in photo.file_path:
                        rel_path = os.path.relpath(photo.file_path, 'uploads')
                        download_url = f"/uploads/{rel_path}"
                    else:
                        logger.warning("   照片 #%d 无法生成下载URL: %s", index + 1, photo.file_path)
            
            photo_data = {
                'id': photo.id,
                'filename': photo.filename,
                'original_filename': photo.original_filename,
                'file_path': photo.file_path,  # 云存储相对路径，如 'photos/user_id/timestamp.jpg'
                'download_url': download_url,  # 预签名下载URL，前端应使用此字段
                'file_size': photo.file_size,
                'mime_type': photo.mime_type,
                'upload_index': photo.upload_index,
                'created_at': photo.created_at.isoformat() + 'Z' if photo.created_at else None,
            }
            photo_responses.append(photo_data)
            
            # 打印每张照片的详细信息
            logger.info("   照片 #%d:", index + 1)
            logger.info("      id: %s", photo.id)
            logger.info("      filename: %s", photo.filename)
            logger.info("      original_filename: %s", photo.original_filename)
            logger.info("      file_path: %s", photo.file_path)
            logger.info("      file_size: %s", photo.file_size)
            logger.info("      upload_index: %s", photo.upload_index)
            logger.info("      created_at: %s", photo.created_at)
            logger.info("      created_at (ISO格式): %s", photo_data['created_at'])
        
        response_data = {
            'order_id': order.id,
            'user_id': order.user_id,
            'store_name': order.store_name,
            'contact_name': order.contact_name,
            'contact_phone': order.contact_phone,
            'contact_address': order.contact_address,
            'status': order.status,
            'total_photos': order.total_photos,
            'photos': photo_responses,
            'created_at': order.created_at.isoformat() + 'Z' if order.created_at else None,
        }
        
        # ========== 响应日志 ==========
        logger.info("=" * 80)
        logger.info("📤 [RESPONSE] GET /api/battery/orders/<order_id>")
        logger.info("   状态码: 200")
        logger.info("   响应数据:")
        logger.info("   order_id: %s", response_data['order_id'])
        logger.info("   user_id: %s", response_data['user_id'])
        logger.info("   store_name: %s", response_data['store_name'])
        logger.info("   status: %s", response_data['status'])
        logger.info("   total_photos: %s", response_data['total_photos'])
        logger.info("   created_at: %s", response_data['created_at'])
        logger.info("   photos 数量: %d", len(response_data['photos']))
        logger.info("   完整响应数据 (JSON):")
        logger.info("   %s", json.dumps(response_data, indent=2, ensure_ascii=False, default=str))
        logger.info("=" * 80)
        
        return make_succ_response(response_data, "获取电池上传订单详情成功"), 200
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ [ERROR] GET /api/battery/orders/<order_id>")
        logger.error("   错误信息: %s", str(e))
        logger.error("=" * 80)
        logger.error("❌ 获取电池订单详情失败: %s", str(e), exc_info=True)
        return make_err_response(f"获取电池订单详情失败: {str(e)}"), 500


def create_battery_order():
    """
    创建电池订单（按重量计价）
    接受云存储路径，不再处理文件上传
    """
    try:
        # ========== 请求日志 ==========
        logger.info("=" * 80)
        logger.info("📥 [REQUEST] POST /api/battery/orders")
        logger.info("📋 请求参数:")
        data = request.get_json()
        logger.info("   request.method: %s", request.method)
        logger.info("   request.url: %s", request.url)
        logger.info("   request.data (JSON):")
        logger.info("   %s", json.dumps(data, indent=2, ensure_ascii=False, default=str) if data else "None")
        logger.info("=" * 80)
        
        if not data:
            logger.warn("⚠️ 请求数据为空")
            return make_err_response("请求数据不能为空"), 400
        
        # 验证请求数据
        if not data.get('batteries') or len(data['batteries']) == 0:
            return make_err_response("电池列表不能为空"), 400
        
        # if not data.get('total_price') or data['total_price'] < 0:
            # return make_err_response("总价格必须>=0"), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return make_err_response("缺少user_id参数"), 400
        
        # 获取用户信息
        user = get_user_registration_by_user_id(user_id)
        if user is None:
            return make_err_response("用户不存在"), 404
        
        # 生成订单ID
        order_id = str(uuid.uuid4())
        
        # 统计照片数量（从电池数据中提取云存储路径）
        photo_count = 0
        batteries = data.get('batteries', [])
        
        # 创建订单记录
        order_data = {
            'id': order_id,
            'user_id': user_id,
            'store_name': user.store_name,
            'contact_name': user.contact_name,
            'contact_phone': user.contact_phone,
            'contact_address': user.address,
            'status': data.get('status', 'pending'),
            'total_photos': 0,  # 将在处理照片后更新
            'pickup_date': datetime.fromisoformat(data['pickup_date'].replace('Z', '+00:00')) if data.get('pickup_date') and data['pickup_date'] else None,
        }
        
        order = create_battery_upload_order(order_data)
        
        # 处理电池照片：保存云存储路径到数据库
        photo_index = 0
        logger.info("📸 开始处理电池照片，batteries 数量: %d", len(batteries))
        
        for battery in batteries:
            image_url = battery.get('image_url')  # 可能是 fileID 或 cloudPath
            file_id = battery.get('file_id')  # 完整的 fileID，格式：cloud://env.storageId/path
            cloud_path = battery.get('cloud_path')  # 云存储相对路径
            
            # 优先使用 file_id，如果没有则使用 image_url
            final_file_id = file_id or (image_url if image_url and image_url.startswith('cloud://') else None)
            final_cloud_path = cloud_path or (image_url if image_url and not image_url.startswith('cloud://') else None)
            
            logger.info("📸 处理电池照片 #%d: image_url = %s, file_id = %s, cloud_path = %s", 
                       photo_index, image_url, file_id, cloud_path)
            
            if final_file_id or final_cloud_path:
                # 从路径中提取文件名
                if final_file_id:
                    # 从 fileID 中提取路径：cloud://env.storageId/path/to/file.jpg
                    path_in_fileid = '/'.join(final_file_id.split('/')[2:]) if '/' in final_file_id else final_file_id
                    path_parts = path_in_fileid.split('/')
                else:
                    # 从 cloudPath 中提取：photos/user_id/timestamp_index.jpg
                    path_parts = final_cloud_path.split('/')
                
                filename = path_parts[-1] if path_parts else f"battery_{photo_index}.jpg"
                original_filename = filename
                
                # 创建照片记录
                # file_path 存储 fileID（如果存在）或 cloudPath
                photo_data = {
                    'id': str(uuid.uuid4()),
                    'order_id': order_id,
                    'user_id': user_id,
                    'filename': filename,
                    'original_filename': original_filename,
                    'file_path': final_file_id or final_cloud_path,  # 优先存储 fileID，如果没有则存储 cloudPath
                    'file_size': 0,  # 云存储路径不包含文件大小信息
                    'mime_type': get_mime_type(filename.split('.')[-1] if '.' in filename else 'jpg'),
                    'upload_index': photo_index,
                }
                
                logger.info("📸 准备插入照片记录: %s", json.dumps(photo_data, indent=2, ensure_ascii=False, default=str))
                
                try:
                    # 直接使用 SQLAlchemy 创建照片记录，避免单独 commit
                    photo = BatteryUploadPhoto(**photo_data)
                    db.session.add(photo)
                    photo_count += 1
                    photo_index += 1
                    logger.info("✅ 照片记录已添加到 session: %s (order_id: %s)", image_url, order_id)
                except Exception as e:
                    logger.error("❌ 添加照片记录失败: %s", str(e), exc_info=True)
                    # 继续处理其他照片，不中断订单创建
            else:
                logger.warn("⚠️ 电池 #%d 没有 image_url 字段", photo_index)
        
        # 更新订单照片数量并提交所有更改（包括照片记录）
        order.total_photos = photo_count
        try:
            db.session.commit()
            logger.info("✅ 数据库事务提交成功，订单照片数量: %d", photo_count)
        except Exception as e:
            logger.error("❌ 数据库事务提交失败: %s", str(e), exc_info=True)
            db.session.rollback()
            raise
        
        logger.info("✅ 成功创建电池订单: %s, 包含 %d 张照片", order_id, photo_count)
        
        # 构建响应数据，只返回云存储路径
        battery_responses = []
        for battery in batteries:
            battery_response = {
                'id': battery.get('id'),
                'type_name': battery.get('type_name'),
                'weight': battery.get('weight'),
                'voltage': battery.get('voltage'),
                'capacity': battery.get('capacity'),
                'price': battery.get('price'),
                'quantity': battery.get('quantity'),
                'image_url': battery.get('image_url'),  # 只返回云存储相对路径
            }
            battery_responses.append(battery_response)
        
        response_data = {
            'order_id': order_id,
            'user_id': user_id,
            'order_type': data.get('order_type', 'weight_based'),
            'batteries': battery_responses,
            'total_price': data['total_price'],
            'total_weight': data.get('total_weight', 0.0),
            'pickup_date': data.get('pickup_date', ''),
            'status': order.status,
            'total_photos': photo_count,
            'created_at': order.created_at.isoformat() + 'Z' if order.created_at else None,
        }
        
        # ========== 响应日志 ==========
        logger.info("=" * 80)
        logger.info("📤 [RESPONSE] POST /api/battery/orders")
        logger.info("   状态码: 200")
        logger.info("   响应数据:")
        logger.info("   order_id: %s", response_data['order_id'])
        logger.info("   user_id: %s", response_data['user_id'])
        logger.info("   order_type: %s", response_data['order_type'])
        logger.info("   total_price: %s", response_data['total_price'])
        logger.info("   total_photos: %s", response_data['total_photos'])
        logger.info("   created_at: %s", response_data['created_at'])
        logger.info("   batteries 数量: %d", len(response_data['batteries']))
        logger.info("   完整响应数据 (JSON):")
        logger.info("   %s", json.dumps(response_data, indent=2, ensure_ascii=False, default=str))
        logger.info("=" * 80)
        
        return make_succ_response(response_data, "电池订单创建成功"), 200
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ [ERROR] POST /api/battery/orders")
        logger.error("   错误信息: %s", str(e))
        logger.error("=" * 80)
        logger.error("❌ 创建电池订单失败: %s", str(e), exc_info=True)
        return make_err_response(f"创建电池订单失败: {str(e)}"), 500

