"""
认证路由 — 注册、登录、个人资料、修改密码
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User
from extensions import db
from routes.helpers import decrypt_secret, encrypt_secret

auth_bp = Blueprint('auth', __name__)


def success(data=None, message='success', code=200):
    """统一成功响应"""
    return jsonify({'code': code, 'message': message, 'data': data}), code


def error(message='error', code=400, data=None):
    """统一错误响应"""
    return jsonify({'code': code, 'message': message, 'data': data}), code


def mask_api_key(api_key):
    if not api_key:
        return ''
    if len(api_key) <= 10:
        return '*' * len(api_key)
    return f'{api_key[:6]}...{api_key[-4:]}'


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return error('用户名、邮箱和密码不能为空', 400)
    if len(username) < 3:
        return error('用户名至少 3 个字符', 400)
    if len(password) < 6:
        return error('密码至少 6 个字符', 400)

    if User.query.filter_by(username=username).first():
        return error('用户名已存在', 400)
    if User.query.filter_by(email=email).first():
        return error('邮箱已被注册', 400)

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return success(user.to_dict(), '注册成功')


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return error('用户名/邮箱和密码不能为空', 400)

    user = User.query.filter(
        db.or_(User.username == username, User.email == username)
    ).first()
    if not user or not user.check_password(password):
        return error('用户名/邮箱或密码错误', 401)

    access_token = create_access_token(identity=str(user.id))
    return success({
        'access_token': access_token,
        'user': user.to_dict(),
    }, '登录成功')


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)
    return success(user.to_dict())


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """修改个人资料"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)

    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    avatar = data.get('avatar', '').strip()

    if username and username != user.username:
        if User.query.filter_by(username=username).first():
            return error('用户名已存在', 400)
        user.username = username
    if email and email != user.email:
        if User.query.filter_by(email=email).first():
            return error('邮箱已被注册', 400)
        user.email = email
    if avatar:
        user.avatar = avatar

    db.session.commit()
    return success(user.to_dict(), '修改成功')


@auth_bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    """修改密码"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)

    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return error('旧密码和新密码不能为空', 400)
    if not user.check_password(old_password):
        return error('旧密码错误', 400)
    if len(new_password) < 6:
        return error('新密码至少 6 个字符', 400)

    user.set_password(new_password)
    db.session.commit()
    return success(None, '密码修改成功')


@auth_bp.route('/ai-key', methods=['GET'])
@jwt_required()
def get_ai_key():
    """获取用户自定义 AI API Key"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)
    return success({
        'has_ai_api_key': bool(decrypt_secret(user.ai_api_key)),
        'masked_ai_api_key': mask_api_key(decrypt_secret(user.ai_api_key)),
    })


@auth_bp.route('/ai-key', methods=['PUT'])
@jwt_required()
def update_ai_key():
    """保存用户自定义 AI API Key"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)
    data = request.get_json(silent=True) or {}
    ai_api_key = data.get('ai_api_key', '').strip()
    user.ai_api_key = encrypt_secret(ai_api_key) if ai_api_key else ''
    db.session.commit()
    return success({
        'has_ai_api_key': bool(ai_api_key),
        'masked_ai_api_key': mask_api_key(ai_api_key),
    }, 'API Key 保存成功')
