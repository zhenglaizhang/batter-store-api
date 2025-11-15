import json

from flask import Response


def make_succ_empty_response():
    """创建成功响应（无数据）"""
    data = json.dumps({
        'success': True,
        'code': 200,
        'message': '操作成功',
        'data': None,
        'error_details': None
    })
    return Response(data, mimetype='application/json')


def make_succ_response(data, message='操作成功'):
    """创建成功响应（有数据）"""
    response_data = {
        'success': True,
        'code': 200,
        'message': message,
        'data': data,
        'error_details': None
    }
    return Response(json.dumps(response_data), mimetype='application/json')


def make_err_response(err_msg, code=400, error_details=None):
    """创建错误响应"""
    response_data = {
        'success': False,
        'code': code,
        'message': err_msg,
        'data': None,
        'error_details': error_details
    }
    return Response(json.dumps(response_data), mimetype='application/json')
