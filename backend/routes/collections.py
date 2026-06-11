"""
知识收藏路由
"""
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Collection
from extensions import db
from ai_client import chat, chat_json
from routes.helpers import API_KEY_NOT_SET_MSG, get_user_api_key, json_body, paged_payload, paginate, wants_paged_response

collections_bp = Blueprint('collections', __name__)


def success(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def error(message='error', code=400, data=None):
    return jsonify({'code': code, 'message': message, 'data': data}), code


@collections_bp.route('', methods=['GET'])
@jwt_required()
def get_collections():
    """获取收藏列表"""
    user_id = int(get_jwt_identity())
    keyword = request.args.get('keyword', '').strip()
    category = request.args.get('category', '').strip()

    query = Collection.query.filter_by(user_id=user_id)
    if keyword:
        query = query.filter(
            db.or_(Collection.title.contains(keyword), Collection.description.contains(keyword))
        )
    if category:
        query = query.filter_by(category=category)

    query = query.order_by(Collection.updated_at.desc())
    if wants_paged_response():
        return success(paged_payload(query, lambda c: c.to_dict()))
    collections = paginate(query).all()
    return success([c.to_dict() for c in collections])


@collections_bp.route('', methods=['POST'])
@jwt_required()
def create_collection():
    """新增收藏"""
    user_id = int(get_jwt_identity())
    data = json_body()

    title = data.get('title', '').strip()
    if not title:
        return error('收藏标题不能为空', 400)

    collection = Collection(
        user_id=user_id,
        title=title,
        url=data.get('url', ''),
        description=data.get('description', ''),
        category=data.get('category', '未分类'),
        tags=json.dumps(data.get('tags', []), ensure_ascii=False),
    )
    db.session.add(collection)
    db.session.commit()
    return success(collection.to_dict(), '创建成功')


@collections_bp.route('/<int:collection_id>', methods=['GET'])
@jwt_required()
def get_collection(collection_id):
    """查看收藏详情"""
    user_id = int(get_jwt_identity())
    collection = Collection.query.filter_by(id=collection_id, user_id=user_id).first()
    if not collection:
        return error('收藏不存在', 404)
    return success(collection.to_dict())


@collections_bp.route('/<int:collection_id>', methods=['PUT'])
@jwt_required()
def update_collection(collection_id):
    """编辑收藏"""
    user_id = int(get_jwt_identity())
    collection = Collection.query.filter_by(id=collection_id, user_id=user_id).first()
    if not collection:
        return error('收藏不存在', 404)

    data = json_body()
    if 'title' in data:
        collection.title = data['title'].strip()
    if 'url' in data:
        collection.url = data['url']
    if 'description' in data:
        collection.description = data['description']
    if 'category' in data:
        collection.category = data['category']
    if 'tags' in data:
        collection.tags = json.dumps(data['tags'], ensure_ascii=False)

    db.session.commit()
    return success(collection.to_dict(), '修改成功')


@collections_bp.route('/<int:collection_id>', methods=['DELETE'])
@jwt_required()
def delete_collection(collection_id):
    """删除收藏"""
    user_id = int(get_jwt_identity())
    collection = Collection.query.filter_by(id=collection_id, user_id=user_id).first()
    if not collection:
        return error('收藏不存在', 404)
    db.session.delete(collection)
    db.session.commit()
    return success(None, '删除成功')


@collections_bp.route('/<int:collection_id>/ai-summary', methods=['POST'])
@jwt_required()
def ai_summary(collection_id):
    """AI 生成收藏摘要"""
    user_id = int(get_jwt_identity())
    collection = Collection.query.filter_by(id=collection_id, user_id=user_id).first()
    if not collection:
        return error('收藏不存在', 404)

    text = collection.title
    if collection.description:
        text += '\n' + collection.description

    try:
        summary = chat(
            f"请用1-2句话概括以下收藏内容的核心价值：\n{text}",
            system_prompt="你是信息摘要专家，简洁精准地概括内容。",
            api_key=get_user_api_key(user_id),
        )
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        summary = (collection.description or collection.title)[:80]
    except Exception:
        summary = (collection.description or collection.title)[:80]

    return success({'summary': summary}, '摘要生成完成')


@collections_bp.route('/<int:collection_id>/ai-tags', methods=['POST'])
@jwt_required()
def ai_tags(collection_id):
    """AI 生成标签"""
    user_id = int(get_jwt_identity())
    collection = Collection.query.filter_by(id=collection_id, user_id=user_id).first()
    if not collection:
        return error('收藏不存在', 404)

    text = collection.title
    if collection.description:
        text += ' ' + collection.description

    try:
        result = chat_json(
            f"为以下收藏内容生成3-5个标签，返回JSON：{{\"tags\":[\"\"]}}\n{text}",
            "你是标签生成专家，只返回JSON。标签应简洁准确。",
            api_key=get_user_api_key(user_id),
        )
        tags = result.get('tags', ['通用']) if result else ['通用']
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        tags = ['通用']
    except Exception:
        tags = ['通用']

    return success({'tags': tags}, '标签生成完成')
