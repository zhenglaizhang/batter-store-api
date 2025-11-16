"""
微信云托管对象存储工具模块
使用 requests 实现文件上传、下载等管理功能
参考：https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloudrun/src/development/storage/service/cos-sdk.html
"""
import logging
import os
import time
import requests
from typing import Optional, Dict, Any
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from qcloud_cos.cos_exception import CosClientError, CosServiceError

logger = logging.getLogger('log')

# 临时密钥缓存
_temp_credentials: Optional[Dict[str, Any]] = None
_temp_credentials_expire_time: int = 0


def get_temp_credentials() -> Optional[Dict[str, Any]]:
    """
    获取临时密钥
    参考：https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloudrun/src/development/storage/service/cos-sdk.html
    :return: 临时密钥字典或 None
    """
    global _temp_credentials, _temp_credentials_expire_time
    
    # 检查缓存是否有效（提前5分钟刷新）
    current_time = int(time.time())
    if _temp_credentials and _temp_credentials_expire_time > current_time + 300:
        return _temp_credentials
    
    try:
        url = "http://api.weixin.qq.com/_/cos/getauth"
        response = requests.get(url, timeout=10, proxies={'http': None, 'https': None})
        response.raise_for_status()
        data = response.json()
        
        if 'TmpSecretId' in data and 'TmpSecretKey' in data:
            _temp_credentials = data
            _temp_credentials_expire_time = int(data.get('ExpiredTime', current_time + 3600))
            logger.info("成功获取临时密钥")
            return _temp_credentials
        else:
            logger.error(f"获取临时密钥失败: {data}")
            return None
    except Exception as e:
        logger.error(f"获取临时密钥异常: {str(e)}", exc_info=True)
        return None


def get_cos_client() -> Optional[CosS3Client]:
    """
    获取 COS 客户端实例（使用临时密钥）
    :return: CosS3Client 实例或 None
    """
    try:
        # 获取临时密钥
        credentials = get_temp_credentials()
        if not credentials:
            logger.error("无法获取临时密钥")
            return None
        
        # 获取存储桶配置
        bucket_name = os.environ.get('COS_BUCKET_NAME')
        region = os.environ.get('COS_REGION', 'ap-shanghai')
        
        if not bucket_name:
            logger.error("缺少 COS 配置: COS_BUCKET_NAME")
            return None
        
        # 使用临时密钥初始化 COS 客户端
        config = CosConfig(
            Region=region,
            SecretId=credentials['TmpSecretId'],
            SecretKey=credentials['TmpSecretKey'],
            Token=credentials.get('Token', ''),
            Scheme='https'
        )
        client = CosS3Client(config)
        logger.info(f"COS 客户端初始化成功，区域: {region}, 存储桶: {bucket_name}")
        return client
    except Exception as e:
        logger.error(f"初始化 COS 客户端失败: {str(e)}", exc_info=True)
        return None


def get_bucket_name() -> Optional[str]:
    """
    获取存储桶名称
    :return: 存储桶名称或 None
    """
    bucket_name = os.environ.get('COS_BUCKET_NAME')
    if not bucket_name:
        logger.error("缺少 COS 配置: COS_BUCKET_NAME")
    return bucket_name


def get_file_metadata(openid: str, cos_path: str) -> Optional[str]:
    """
    获取文件元数据（用于小程序端访问）
    参考：https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloudrun/src/development/storage/service/cos-sdk.html
    :param openid: 用户 openid，管理端传空字符串
    :param cos_path: COS 文件路径
    :return: 元数据字符串或 None
    """
    try:
        bucket_name = get_bucket_name()
        if not bucket_name:
            return None
        
        url = "https://api.weixin.qq.com/_/cos/metaid/encode"
        payload = {
            "openid": openid,
            "bucket": bucket_name,
            "paths": [cos_path]
        }
        
        response = requests.post(url, json=payload, timeout=10, proxies={'http': None, 'https': None})
        response.raise_for_status()
        data = response.json()
        
        if data.get('errcode') == 0 and data.get('respdata'):
            metaid = data['respdata'].get('x_cos_meta_field_strs', [])
            if metaid:
                logger.info(f"成功获取文件元数据: {cos_path}")
                return metaid[0]
        
        logger.error(f"获取文件元数据失败: {data}")
        return None
    except Exception as e:
        logger.error(f"获取文件元数据异常: {str(e)}", exc_info=True)
        return None


def upload_photo_to_cos(file_data: bytes, user_id: str, filename: str, openid: str = '') -> Optional[str]:
    """
    上传照片到微信云托管对象存储
    :param file_data: 文件数据（字节）
    :param user_id: 用户ID
    :param filename: 文件名
    :param openid: 用户 openid，管理端传空字符串
    :return: COS 文件路径（Key）或 None
    """
    try:
        client = get_cos_client()
        if not client:
            return None
        
        bucket_name = get_bucket_name()
        if not bucket_name:
            return None
        
        # 构建 COS 文件路径（Key）
        # 格式: photos/{user_id}/{filename}
        cos_key = f"photos/{user_id}/{filename}"
        
        # 获取文件元数据（重要：小程序端访问必需）
        metaid = get_file_metadata(openid, cos_key)
        if not metaid:
            logger.warning(f"无法获取文件元数据，但继续上传: {cos_key}")
        
        # 准备上传参数
        put_params = {
            'Bucket': bucket_name,
            'Body': file_data,
            'Key': cos_key,
            'StorageClass': 'STANDARD'
        }
        
        # 如果有元数据，添加到 Headers
        if metaid:
            put_params['Headers'] = {
                'x-cos-meta-fileid': metaid
            }
        
        # 上传文件
        response = client.put_object(**put_params)
        
        if response.get('ETag'):
            logger.info(f"文件上传成功到 COS: {cos_key}, ETag: {response.get('ETag')}")
            return cos_key
        else:
            logger.error(f"文件上传失败: {response}")
            return None
        
    except CosClientError as e:
        logger.error(f"COS 客户端错误: {str(e)}", exc_info=True)
        return None
    except CosServiceError as e:
        logger.error(f"COS 服务错误: {e.get_error_code()}, {e.get_error_msg()}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"上传文件到 COS 失败: {str(e)}", exc_info=True)
        return None


def get_file_download_url(cos_key: str, expires: int = 3600) -> Optional[str]:
    """
    获取文件的预签名下载URL
    :param cos_key: COS 文件路径（Key）
    :param expires: URL 有效期（秒），默认 3600 秒（1小时）
    :return: 预签名下载URL或 None
    """
    try:
        client = get_cos_client()
        if not client:
            return None
        
        bucket_name = get_bucket_name()
        if not bucket_name:
            return None
        
        # 生成预签名URL
        url = client.get_presigned_download_url(
            Bucket=bucket_name,
            Key=cos_key,
            Expired=expires
        )
        
        logger.info(f"获取下载URL成功: {cos_key}, 有效期: {expires}秒")
        return url
        
    except CosClientError as e:
        logger.error(f"COS 客户端错误: {str(e)}", exc_info=True)
        return None
    except CosServiceError as e:
        logger.error(f"COS 服务错误: {e.get_error_code()}, {e.get_error_msg()}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"获取下载URL失败: {str(e)}", exc_info=True)
        return None


def download_file_from_cos(cos_key: str, local_path: str) -> bool:
    """
    从 COS 下载文件到本地
    :param cos_key: COS 文件路径（Key）
    :param local_path: 本地保存路径
    :return: 是否成功
    """
    try:
        client = get_cos_client()
        if not client:
            return False
        
        bucket_name = get_bucket_name()
        if not bucket_name:
            return False
        
        # 确保本地目录存在
        os.makedirs(os.path.dirname(local_path) if os.path.dirname(local_path) else '.', exist_ok=True)
        
        # 下载文件
        response = client.get_object(
            Bucket=bucket_name,
            Key=cos_key
        )
        response['Body'].get_stream_to_file(local_path)
        
        logger.info(f"文件下载成功: {cos_key} -> {local_path}")
        return True
        
    except CosClientError as e:
        logger.error(f"COS 客户端错误: {str(e)}", exc_info=True)
        return False
    except CosServiceError as e:
        logger.error(f"COS 服务错误: {e.get_error_code()}, {e.get_error_msg()}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}", exc_info=True)
        return False


def delete_file_from_cos(cos_key: str) -> bool:
    """
    从 COS 删除文件
    :param cos_key: COS 文件路径（Key）
    :return: 是否成功
    """
    try:
        client = get_cos_client()
        if not client:
            return False
        
        bucket_name = get_bucket_name()
        if not bucket_name:
            return False
        
        # 删除文件
        client.delete_object(
            Bucket=bucket_name,
            Key=cos_key
        )
        
        logger.info(f"文件删除成功: {cos_key}")
        return True
        
    except CosClientError as e:
        logger.error(f"COS 客户端错误: {str(e)}", exc_info=True)
        return False
    except CosServiceError as e:
        logger.error(f"COS 服务错误: {e.get_error_code()}, {e.get_error_msg()}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}", exc_info=True)
        return False


def decode_file_metadata(metaid: str) -> Optional[Dict[str, Any]]:
    """
    解析文件元数据
    参考：https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloudrun/src/development/storage/service/cos-sdk.html
    :param metaid: 元数据字符串
    :return: 解析后的元数据字典或 None
    """
    try:
        url = "https://api.weixin.qq.com/_/cos/metaid/decode"
        payload = {
            "metaid": metaid
        }
        
        response = requests.post(url, json=payload, timeout=10, proxies={'http': None, 'https': None})
        response.raise_for_status()
        data = response.json()
        
        if data.get('errcode') == 0 and data.get('respdata'):
            raw_data = data['respdata'].get('raw_data', {})
            logger.info(f"成功解析文件元数据: {raw_data}")
            return raw_data
        
        logger.error(f"解析文件元数据失败: {data}")
        return None
    except Exception as e:
        logger.error(f"解析文件元数据异常: {str(e)}", exc_info=True)
        return None
