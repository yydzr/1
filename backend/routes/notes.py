"""
笔记管理路由
"""
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Note
from extensions import db
from ai_client import chat, chat_json
from routes.helpers import API_KEY_NOT_SET_MSG, get_user_api_key, json_body, paged_payload, paginate, wants_paged_response

notes_bp = Blueprint('notes', __name__)


def success(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def error(message='error', code=400, data=None):
    return jsonify({'code': code, 'message': message, 'data': data}), code


@notes_bp.route('', methods=['GET'])
@jwt_required()
def get_notes():
    """获取笔记列表"""
    user_id = int(get_jwt_identity())
    keyword = request.args.get('keyword', '').strip()
    category = request.args.get('category', '').strip()

    query = Note.query.filter_by(user_id=user_id)
    if keyword:
        query = query.filter(
            db.or_(Note.title.contains(keyword), Note.content.contains(keyword))
        )
    if category:
        query = query.filter_by(category=category)

    query = query.order_by(Note.is_top.desc(), Note.updated_at.desc())
    if wants_paged_response():
        return success(paged_payload(query, lambda n: n.to_dict()))
    notes = paginate(query).all()
    return success([n.to_dict() for n in notes])


@notes_bp.route('', methods=['POST'])
@jwt_required()
def create_note():
    """新增笔记"""
    user_id = int(get_jwt_identity())
    data = json_body()

    title = data.get('title', '').strip()
    if not title:
        return error('笔记标题不能为空', 400)

    note = Note(
        user_id=user_id,
        title=title,
        content=data.get('content', ''),
        category=data.get('category', '未分类'),
        tags=json.dumps(data.get('tags', []), ensure_ascii=False),
        is_top=data.get('is_top', False),
        is_favorite=data.get('is_favorite', False),
        note_color=data.get('note_color', '#ffffff'),
    )
    db.session.add(note)
    db.session.commit()
    return success(note.to_dict(), '创建成功')


@notes_bp.route('/<int:note_id>', methods=['GET'])
@jwt_required()
def get_note(note_id):
    """查看笔记详情"""
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return error('笔记不存在', 404)
    return success(note.to_dict())


@notes_bp.route('/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_note(note_id):
    """编辑笔记"""
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return error('笔记不存在', 404)

    data = json_body()
    if 'title' in data:
        note.title = data['title'].strip()
    if 'content' in data:
        note.content = data['content']
    if 'category' in data:
        note.category = data['category']
    if 'tags' in data:
        note.tags = json.dumps(data['tags'], ensure_ascii=False)
    if 'is_top' in data:
        note.is_top = data['is_top']
    if 'is_favorite' in data:
        note.is_favorite = data['is_favorite']
    if 'is_archived' in data:
        note.is_archived = data['is_archived']
    if 'note_color' in data:
        note.note_color = data['note_color']

    db.session.commit()
    return success(note.to_dict(), '修改成功')


@notes_bp.route('/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(note_id):
    """删除笔记"""
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return error('笔记不存在', 404)
    db.session.delete(note)
    db.session.commit()
    return success(None, '删除成功')


@notes_bp.route('/<int:note_id>/top', methods=['PATCH'])
@jwt_required()
def toggle_top(note_id):
    """切换置顶"""
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return error('笔记不存在', 404)
    note.is_top = not note.is_top
    db.session.commit()
    return success(note.to_dict(), '操作成功')


@notes_bp.route('/<int:note_id>/favorite', methods=['PATCH'])
@jwt_required()
def toggle_favorite(note_id):
    """切换收藏"""
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return error('笔记不存在', 404)
    note.is_favorite = not note.is_favorite
    db.session.commit()
    return success(note.to_dict(), '操作成功')


@notes_bp.route('/<int:note_id>/archive', methods=['PATCH'])
@jwt_required()
def toggle_archive(note_id):
    """切换归档"""
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return error('笔记不存在', 404)
    note.is_archived = not note.is_archived
    db.session.commit()
    return success(note.to_dict(), '操作成功')


@notes_bp.route('/<int:note_id>/summary', methods=['POST'])
@jwt_required()
def ai_summary(note_id):
    """AI 总结笔记"""
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return error('笔记不存在', 404)

    content = note.content or ''
    if not content.strip():
        return success({'summary': '内容为空，无法总结', 'note_id': note_id})

    try:
        summary = chat(
            f"请用1-3句话总结以下笔记内容，提取核心要点：\n\n{content}",
            system_prompt="你是专业的笔记总结助手，简洁精准地提炼核心信息。",
            api_key=get_user_api_key(user_id),
        )
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        summary = content[:100] + '...' if len(content) > 100 else content
    except Exception:
        summary = content[:100] + '...' if len(content) > 100 else content

    return success({'summary': summary, 'note_id': note_id}, 'AI 总结完成')


@notes_bp.route('/classify', methods=['POST'])
@jwt_required()
def ai_classify():
    """AI 自动分类"""
    user_id = int(get_jwt_identity())
    data = json_body()
    title = data.get('title', '')
    content = data.get('content', '')

    if not title and not content:
        return error('请提供标题或内容', 400)

    cat_list = '工作、学习、生活、技术、读书、其他'
    try:
        result = chat_json(
            f"请将以下笔记分类。可选分类：{cat_list}\n标题：{title}\n内容：{content}\n返回JSON：{{\"category\":\"\"}}",
            "你只返回JSON，根据笔记主题选择最合适的分类。",
            api_key=get_user_api_key(user_id),
        )
        category = result.get('category', '其他') if result else '其他'
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        category = '其他'
    except Exception:
        category = '其他'

    return success({'category': category}, '分类完成')


@notes_bp.route('/keywords', methods=['POST'])
@jwt_required()
def ai_keywords():
    """AI 提取关键词"""
    user_id = int(get_jwt_identity())
    data = json_body()
    title = data.get('title', '')
    content = data.get('content', '')

    if not title and not content:
        return error('请提供标题或内容', 400)

    try:
        result = chat_json(
            f"从以下笔记中提取3-5个关键词，只返回最有代表性的关键词。\n标题：{title}\n内容：{content}\n返回JSON：{{\"keywords\":[\"\",\"\"]}}",
            "你是关键词提取专家，只返回JSON数组。",
            api_key=get_user_api_key(user_id),
        )
        keywords = result.get('keywords', ['通用']) if result else ['通用']
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        keywords = ['通用']
    except Exception:
        keywords = ['通用']

    return success({'keywords': keywords}, '提取完成')


@notes_bp.route('/generate-title', methods=['POST'])
@jwt_required()
def ai_generate_title():
    """AI 生成标题"""
    user_id = int(get_jwt_identity())
    data = json_body()
    content = data.get('content', '')

    if not content:
        return error('内容不能为空', 400)

    try:
        result = chat_json(
            f"为以下笔记内容生成一个简练的标题（15字以内）：\n{content}\n返回JSON：{{\"title\":\"\"}}",
            "你只返回JSON，只生成标题。",
            api_key=get_user_api_key(user_id),
        )
        title = result.get('title', content[:30]) if result else content[:30]
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        title = content[:30]
    except Exception:
        title = content[:30]

    return success({'title': title}, '标题生成完成')
