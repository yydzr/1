"""
待办任务路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models import Todo
from extensions import db
from ai_client import chat, chat_json
from routes.helpers import API_KEY_NOT_SET_MSG, get_user_api_key, json_body, paged_payload, paginate, wants_paged_response

todos_bp = Blueprint('todos', __name__)


def success(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def error(message='error', code=400, data=None):
    return jsonify({'code': code, 'message': message, 'data': data}), code


@todos_bp.route('', methods=['GET'])
@jwt_required()
def get_todos():
    """获取待办列表"""
    user_id = int(get_jwt_identity())
    status = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()
    category = request.args.get('category', '').strip()

    query = Todo.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if category:
        query = query.filter_by(category=category)

    query = query.order_by(
        Todo.priority.desc(),
        Todo.due_date.asc(),
        Todo.created_at.desc()
    )
    if wants_paged_response():
        return success(paged_payload(query, lambda t: t.to_dict()))
    todos = paginate(query).all()
    return success([t.to_dict() for t in todos])


@todos_bp.route('', methods=['POST'])
@jwt_required()
def create_todo():
    """新增待办"""
    user_id = int(get_jwt_identity())
    data = json_body()

    title = data.get('title', '').strip()
    if not title:
        return error('待办标题不能为空', 400)

    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            try:
                due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except (ValueError, TypeError):
                pass

    todo = Todo(
        user_id=user_id,
        title=title,
        description=data.get('description', ''),
        priority=data.get('priority', '中'),
        status=data.get('status', '未完成'),
        category=data.get('category', '默认'),
        progress=data.get('progress', 0),
        due_date=due_date,
    )
    db.session.add(todo)
    db.session.commit()
    return success(todo.to_dict(), '创建成功')


@todos_bp.route('/<int:todo_id>', methods=['GET'])
@jwt_required()
def get_todo(todo_id):
    """查看待办详情"""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return error('待办不存在', 404)
    return success(todo.to_dict())


@todos_bp.route('/<int:todo_id>', methods=['PUT'])
@jwt_required()
def update_todo(todo_id):
    """编辑待办"""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return error('待办不存在', 404)

    data = json_body()
    if 'title' in data:
        todo.title = data['title'].strip()
    if 'description' in data:
        todo.description = data['description']
    if 'priority' in data:
        todo.priority = data['priority']
    if 'status' in data:
        todo.status = data['status']
    if 'category' in data:
        todo.category = data['category']
    if 'progress' in data:
        todo.progress = data['progress']
    if 'due_date' in data:
        due_date = data['due_date']
        if due_date:
            try:
                todo.due_date = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                try:
                    todo.due_date = datetime.strptime(due_date, '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
        else:
            todo.due_date = None

    db.session.commit()
    return success(todo.to_dict(), '修改成功')


@todos_bp.route('/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def delete_todo(todo_id):
    """删除待办"""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return error('待办不存在', 404)
    db.session.delete(todo)
    db.session.commit()
    return success(None, '删除成功')


@todos_bp.route('/<int:todo_id>/toggle', methods=['PATCH'])
@jwt_required()
def toggle_todo(todo_id):
    """切换完成状态"""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return error('待办不存在', 404)
    if todo.status == '已完成':
        todo.status = '未完成'
        todo.progress = 0
    else:
        todo.status = '已完成'
        todo.progress = 100
    db.session.commit()
    return success(todo.to_dict(), '操作成功')


@todos_bp.route('/<int:todo_id>/progress', methods=['PATCH'])
@jwt_required()
def update_progress(todo_id):
    """更新任务进度"""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return error('待办不存在', 404)

    data = json_body()
    progress = data.get('progress', 0)
    todo.progress = max(0, min(100, progress))
    if todo.progress >= 100:
        todo.status = '已完成'
    db.session.commit()
    return success(todo.to_dict(), '进度更新成功')


@todos_bp.route('/today', methods=['GET'])
@jwt_required()
def today_todos():
    """获取今日待办"""
    user_id = int(get_jwt_identity())
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    todos = Todo.query.filter(
        Todo.user_id == user_id,
        Todo.status == '未完成',
        Todo.due_date.isnot(None),
        Todo.due_date >= today,
        Todo.due_date < tomorrow,
    ).order_by(Todo.priority.desc(), Todo.created_at.desc()).all()
    return success([t.to_dict() for t in todos])


@todos_bp.route('/overdue', methods=['GET'])
@jwt_required()
def overdue_todos():
    """获取逾期待办"""
    user_id = int(get_jwt_identity())
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    todos = Todo.query.filter(
        Todo.user_id == user_id,
        Todo.status == '未完成',
        Todo.due_date.isnot(None),
        Todo.due_date < today
    ).order_by(Todo.due_date.asc()).all()
    return success([t.to_dict() for t in todos])


@todos_bp.route('/ai-generate', methods=['POST'])
@jwt_required()
def ai_generate():
    """AI 根据一句话生成待办"""
    user_id = int(get_jwt_identity())
    data = json_body()
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return error('请输入描述', 400)

    try:
        result = chat_json(
            f"根据用户描述生成一个待办事项，返回JSON：{{\"title\":\"\", \"description\":\"\", \"priority\":\"\", \"category\":\"\"}}\n用户描述：{prompt}\n\n优先级从 高/中/低 中选择，分类用简短标签（如 工作/学习/个人等）。",
            "你是任务管理助手，只返回JSON。",
            api_key=get_user_api_key(user_id),
        )
        if result:
            todo = {
                'title': result.get('title', prompt),
                'description': result.get('description', ''),
                'priority': result.get('priority', '中'),
                'category': result.get('category', 'AI 生成'),
                'progress': 0,
            }
        else:
            todo = {'title': prompt, 'description': '', 'priority': '中', 'category': 'AI 生成', 'progress': 0}
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        todo = {'title': prompt, 'description': '', 'priority': '中', 'category': 'AI 生成', 'progress': 0}
    except Exception:
        todo = {'title': prompt, 'description': '', 'priority': '中', 'category': 'AI 生成', 'progress': 0}

    return success(todo, 'AI 生成完成')


@todos_bp.route('/ai-split', methods=['POST'])
@jwt_required()
def ai_split():
    """AI 拆分复杂任务"""
    user_id = int(get_jwt_identity())
    data = json_body()
    task_title = data.get('title', '').strip()
    if not task_title:
        return error('请提供任务标题', 400)

    try:
        result = chat_json(
            f"将以下复杂任务拆分为3-5个子任务步骤，返回JSON：{{\"subtasks\":[{{\"title\":\"\",\"priority\":\"\"}}]}}\n任务：{task_title}\n优先级从 高/中/低 中选择。",
            "你是任务拆分专家，只返回JSON。",
            api_key=get_user_api_key(user_id),
        )
        subtasks = result.get('subtasks', []) if result else []
        if not subtasks:
            subtasks = [{'title': f'{task_title} - 步骤{i+1}', 'priority': '中'} for i in range(3)]
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        subtasks = [{'title': f'{task_title} - 步骤{i+1}', 'priority': '中'} for i in range(3)]
    except Exception:
        subtasks = [{'title': f'{task_title} - 步骤{i+1}', 'priority': '中'} for i in range(3)]

    return success({'subtasks': subtasks}, '拆分完成')


@todos_bp.route('/ai-priority', methods=['POST'])
@jwt_required()
def ai_priority():
    """AI 推荐任务优先级"""
    user_id = int(get_jwt_identity())
    data = json_body()
    title = data.get('title', '').strip()
    description = data.get('description', '')

    try:
        result = chat_json(
            f"根据任务信息推荐优先级（高/中/低），返回JSON：{{\"priority\":\"\", \"reason\":\"\"}}\n标题：{title}\n描述：{description}",
            "你是任务优先级评估专家，只返回JSON。",
            api_key=get_user_api_key(user_id),
        )
        priority = result.get('priority', '中') if result else '中'
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        priority = '中'
    except Exception:
        priority = '中'

    return success({'priority': priority}, '推荐完成')
