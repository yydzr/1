import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from flask import request

from config import Config


API_KEY_NOT_SET_MSG = '请先在个人中心设置你的 DeepSeek API Key，获取地址: https://platform.deepseek.com/api_keys'


def json_body():
    return request.get_json(silent=True) or {}


def pagination(default_per_page=100, max_per_page=200):
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get('per_page', default_per_page))
    except (TypeError, ValueError):
        per_page = default_per_page
    per_page = min(max(1, per_page), max_per_page)
    return page, per_page


def paginate(query, default_per_page=100, max_per_page=200):
    page, per_page = pagination(default_per_page, max_per_page)
    return query.offset((page - 1) * per_page).limit(per_page)


def paged_payload(query, serializer, default_per_page=12, max_per_page=100):
    page, per_page = pagination(default_per_page, max_per_page)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        'items': [serializer(item) for item in items],
        'total': total,
        'page': page,
        'per_page': per_page,
    }


def wants_paged_response():
    return request.args.get('include_total') == '1'


def get_user_api_key(user_id):
    from models import User
    user = User.query.get(user_id)
    return decrypt_secret(user.ai_api_key) if user and user.ai_api_key else None


def _fernet():
    key = base64.urlsafe_b64encode(hashlib.sha256(Config.SECRET_KEY.encode('utf-8')).digest())
    return Fernet(key)


def encrypt_secret(value):
    if not value:
        return ''
    if value.startswith('enc:'):
        return value
    return 'enc:' + _fernet().encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt_secret(value):
    if not value:
        return ''
    if not value.startswith('enc:'):
        return value
    try:
        return _fernet().decrypt(value[4:].encode('utf-8')).decode('utf-8')
    except (InvalidToken, ValueError):
        return ''
