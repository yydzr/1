"""
全局搜索路由
跨笔记、待办、日程、目标、收藏统一检索
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from models import Collection, Goal, Note, Schedule, Todo

search_bp = Blueprint('search', __name__)


def success(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def _limit():
    try:
        value = int(request.args.get('limit', 6))
    except (TypeError, ValueError):
        value = 6
    return min(max(1, value), 20)


def _excerpt(*values):
    for value in values:
        if value:
            text = str(value).replace('\n', ' ').strip()
            if text:
                return text[:120]
    return ''


def _group(key, label, items, total):
    return {
        'key': key,
        'label': label,
        'total': total,
        'items': items,
    }


@search_bp.route('', methods=['GET'])
@jwt_required()
def global_search():
    """全局搜索"""
    user_id = int(get_jwt_identity())
    keyword = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all').strip() or 'all'
    per_group = _limit()

    if not keyword:
        return success({
            'keyword': '',
            'total': 0,
            'groups': [],
        })

    like = f'%{keyword}%'
    groups = []

    if search_type in ('all', 'notes'):
        query = Note.query.filter(
            Note.user_id == user_id,
            Note.is_archived == False,  # noqa: E712
            or_(
                Note.title.ilike(like),
                Note.content.ilike(like),
                Note.category.ilike(like),
                Note.tags.ilike(like),
            ),
        ).order_by(Note.updated_at.desc())
        notes = [{
            'type': 'notes',
            'type_label': '笔记',
            'id': item.id,
            'title': item.title,
            'summary': _excerpt(item.content, item.category),
            'meta': item.updated_at.strftime('%Y-%m-%d') if item.updated_at else '',
            'path': f'/notes/{item.id}',
        } for item in query.limit(per_group).all()]
        groups.append(_group('notes', '笔记', notes, query.count()))

    if search_type in ('all', 'todos'):
        query = Todo.query.filter(
            Todo.user_id == user_id,
            or_(
                Todo.title.ilike(like),
                Todo.description.ilike(like),
                Todo.category.ilike(like),
                Todo.priority.ilike(like),
                Todo.status.ilike(like),
            ),
        ).order_by(Todo.updated_at.desc())
        todos = [{
            'type': 'todos',
            'type_label': '待办',
            'id': item.id,
            'title': item.title,
            'summary': _excerpt(item.description, item.category),
            'meta': item.status,
            'path': '/todos',
        } for item in query.limit(per_group).all()]
        groups.append(_group('todos', '待办', todos, query.count()))

    if search_type in ('all', 'schedules'):
        query = Schedule.query.filter(
            Schedule.user_id == user_id,
            or_(
                Schedule.title.ilike(like),
                Schedule.description.ilike(like),
                Schedule.location.ilike(like),
            ),
        ).order_by(Schedule.start_time.desc())
        schedules = [{
            'type': 'schedules',
            'type_label': '日程',
            'id': item.id,
            'title': item.title,
            'summary': _excerpt(item.description, item.location),
            'meta': item.start_time.strftime('%Y-%m-%d %H:%M') if item.start_time else '',
            'path': '/schedules',
        } for item in query.limit(per_group).all()]
        groups.append(_group('schedules', '日程', schedules, query.count()))

    if search_type in ('all', 'goals'):
        query = Goal.query.filter(
            Goal.user_id == user_id,
            or_(
                Goal.title.ilike(like),
                Goal.description.ilike(like),
                Goal.status.ilike(like),
            ),
        ).order_by(Goal.updated_at.desc())
        goals = [{
            'type': 'goals',
            'type_label': '目标',
            'id': item.id,
            'title': item.title,
            'summary': _excerpt(item.description, item.status),
            'meta': f'{item.progress or 0}%',
            'path': '/goals',
        } for item in query.limit(per_group).all()]
        groups.append(_group('goals', '目标', goals, query.count()))

    if search_type in ('all', 'collections'):
        query = Collection.query.filter(
            Collection.user_id == user_id,
            or_(
                Collection.title.ilike(like),
                Collection.description.ilike(like),
                Collection.url.ilike(like),
                Collection.category.ilike(like),
                Collection.tags.ilike(like),
            ),
        ).order_by(Collection.updated_at.desc())
        collections = [{
            'type': 'collections',
            'type_label': '收藏',
            'id': item.id,
            'title': item.title,
            'summary': _excerpt(item.description, item.url, item.category),
            'meta': item.category,
            'path': '/collections',
        } for item in query.limit(per_group).all()]
        groups.append(_group('collections', '收藏', collections, query.count()))

    return success({
        'keyword': keyword,
        'total': sum(group['total'] for group in groups),
        'groups': groups,
    })
