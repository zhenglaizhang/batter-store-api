import logging
import os
import uuid
from datetime import datetime
from flask import request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from wxcloudrun import db
from wxcloudrun.dao import (
    get_user_registration_by_user_id, create_battery_upload_order,
    get_all_battery_upload_orders, get_battery_upload_order_by_id,
    create_battery_upload_photo, get_photos_by_order_id,
    update_user_business_license_path
)
from wxcloudrun.utils import is_valid_image_type, get_mime_type
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.cos_storage import upload_photo_to_cos, get_file_download_url

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
                if not cos_key:
                    logger.error("上传文件到 COS 失败: %s", original_filename)
                    continue
                
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
                
                # 获取下载URL（预签名URL，有效期1小时）
                download_url = get_file_download_url(cos_key, expires=3600)
                
                photos.append({
                    'id': photo.id,
                    'filename': photo.filename,
                    'original_filename': photo.original_filename,
                    'cos_key': cos_key,  # COS 文件路径（Key）
                    'file_path': photo.file_path,  # 兼容旧字段，实际存储的是COS Key
                    'download_url': download_url,  # 预签名下载URL
                    'file_size': photo.file_size,
                    'mime_type': photo.mime_type,
                    'upload_index': photo.upload_index,
                    'created_at': photo.created_at.isoformat() + 'Z' if photo.created_at else None,
                })
                
                logger.info("文件上传成功到 COS: %s, cos_key: %s", unique_filename, cos_key)
            
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
        logger.info("🚀 开始获取所有电池上传订单")
        
        orders = get_all_battery_upload_orders()
        
        order_responses = []
        for order in orders:
            # 获取每个订单的照片
            photos = get_photos_by_order_id(order.id)
            
            photo_responses = []
            for photo in photos:
                # 获取下载URL（如果 file_path 是 COS Key）
                download_url = None
                if photo.file_path and not photo.file_path.startswith('/') and photo.file_path.startswith('photos/'):
                    # 是 COS Key，获取预签名下载URL
                    download_url = get_file_download_url(photo.file_path, expires=3600)
                
                photo_responses.append({
                    'id': photo.id,
                    'filename': photo.filename,
                    'original_filename': photo.original_filename,
                    'cos_key': photo.file_path if photo.file_path and not photo.file_path.startswith('/') and photo.file_path.startswith('photos/') else None,
                    'file_path': photo.file_path,
                    'download_url': download_url,
                    'file_size': photo.file_size,
                    'mime_type': photo.mime_type,
                    'upload_index': photo.upload_index,
                    'created_at': photo.created_at.isoformat() + 'Z' if photo.created_at else None,
                })
            
            order_responses.append({
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
            })
        
        logger.info("✅ 成功获取电池上传订单，共 %d 个", len(order_responses))
        return make_succ_response(order_responses, "获取电池上传订单成功"), 200
        
    except Exception as e:
        logger.error("❌ 获取电池订单失败: %s", str(e), exc_info=True)
        return make_err_response(f"获取电池订单失败: {str(e)}"), 500


def get_battery_order_detail(order_id):
    """
    获取电池上传订单详情（管理员功能）
    """
    try:
        logger.info("🚀 开始获取电池上传订单详情: %s", order_id)
        
        order = get_battery_upload_order_by_id(order_id)
        if order is None:
            logger.warn("⚠️ 未找到指定的电池订单: %s", order_id)
            return make_err_response("未找到指定的电池订单"), 404
        
        # 获取订单照片
        photos = get_photos_by_order_id(order_id)
        
        photo_responses = []
        for photo in photos:
            # 获取下载URL（如果 file_path 是 COS Key）
            download_url = None
            if photo.file_path and not photo.file_path.startswith('/') and photo.file_path.startswith('photos/'):
                # 是 COS Key，获取预签名下载URL
                download_url = get_file_download_url(photo.file_path, expires=3600)
            
            photo_responses.append({
                'id': photo.id,
                'filename': photo.filename,
                'original_filename': photo.original_filename,
                'cos_key': photo.file_path if photo.file_path and not photo.file_path.startswith('/') and photo.file_path.startswith('photos/') else None,
                'file_path': photo.file_path,
                'download_url': download_url,
                'file_size': photo.file_size,
                'mime_type': photo.mime_type,
                'upload_index': photo.upload_index,
                'created_at': photo.created_at.isoformat() + 'Z' if photo.created_at else None,
            })
        
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
        
        logger.info("✅ 成功获取电池上传订单详情: %s", order_id)
        return make_succ_response(response_data, "获取电池上传订单详情成功"), 200
        
    except Exception as e:
        logger.error("❌ 获取电池订单详情失败: %s", str(e), exc_info=True)
        return make_err_response(f"获取电池订单详情失败: {str(e)}"), 500


def create_battery_order():
    """
    创建电池订单（按重量计价）
    """
    try:
        logger.info("🚀 开始创建电池订单")
        data = request.get_json()
        
        if not data:
            return make_err_response("请求数据不能为空"), 400
        
        # 验证请求数据
        if not data.get('batteries') or len(data['batteries']) == 0:
            return make_err_response("电池列表不能为空"), 400
        
        if not data.get('total_price') or data['total_price'] <= 0:
            return make_err_response("总价格必须大于0"), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return make_err_response("缺少user_id参数"), 400
        
        # 获取用户信息
        user = get_user_registration_by_user_id(user_id)
        if user is None:
            return make_err_response("用户不存在"), 404
        
        # 生成订单ID
        order_id = str(uuid.uuid4())
        
        # 创建订单记录
        order_data = {
            'id': order_id,
            'user_id': user_id,
            'store_name': user.store_name,
            'contact_name': user.contact_name,
            'contact_phone': user.contact_phone,
            'contact_address': user.address,
            'status': data.get('status', 'pending'),
            'total_photos': 0,
            'pickup_date': datetime.fromisoformat(data['pickup_date'].replace('Z', '+00:00')) if data.get('pickup_date') else None,
        }
        
        order = create_battery_upload_order(order_data)
        
        logger.info("✅ 成功创建电池订单: %s", order_id)
        
        response_data = {
            'order_id': order_id,
            'user_id': user_id,
            'order_type': data.get('order_type', 'weight_based'),
            'total_price': data['total_price'],
            'total_weight': data.get('total_weight', 0.0),
            'pickup_date': data.get('pickup_date', ''),
            'status': order.status,
            'created_at': order.created_at.isoformat() + 'Z' if order.created_at else None,
        }
        
        return make_succ_response(response_data, "电池订单创建成功"), 200
        
    except Exception as e:
        logger.error("❌ 创建电池订单失败: %s", str(e), exc_info=True)
        return make_err_response(f"创建电池订单失败: {str(e)}"), 500

