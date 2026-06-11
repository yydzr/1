"""
目标管理路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import Goal
from extensions import db
from ai_client import chat_json
from routes.helpers import API_KEY_NOT_SET_MSG, get_user_api_key, json_body, paged_payload, paginate, wants_paged_response

goals_bp = Blueprint('goals', __name__)


def success(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def error(message='error', code=400, data=None):
    return jsonify({'code': code, 'message': message, 'data': data}), code


@goals_bp.route('', methods=['GET'])
@jwt_required()
def get_goals():
    """获取目标列表"""
    user_id = int(get_jwt_identity())
    status = request.args.get('status', '').strip()

    query = Goal.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Goal.progress.asc(), Goal.end_date.asc())
    if wants_paged_response():
        return success(paged_payload(query, lambda g: g.to_dict()))
    goals = paginate(query).all()
    return success([g.to_dict() for g in goals])


@goals_bp.route('', methods=['POST'])
@jwt_required()
def create_goal():
    """新增目标"""
    user_id = int(get_jwt_identity())
    data = json_body()

    title = data.get('title', '').strip()
    if not title:
        return error('目标标题不能为空', 400)

    start_date = None
    if data.get('start_date'):
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        except (ValueError, TypeError):
            pass

    end_date = None
    if data.get('end_date'):
        try:
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        except (ValueError, TypeError):
            pass

    goal = Goal(
        user_id=user_id,
        title=title,
        description=data.get('description', ''),
        progress=data.get('progress', 0),
        status=data.get('status', '进行中'),
        start_date=start_date,
        end_date=end_date,
    )
    db.session.add(goal)
    db.session.commit()
    return success(goal.to_dict(), '创建成功')


@goals_bp.route('/<int:goal_id>', methods=['GET'])
@jwt_required()
def get_goal(goal_id):
    """查看目标详情"""
    user_id = int(get_jwt_identity())
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return error('目标不存在', 404)
    return success(goal.to_dict())


@goals_bp.route('/<int:goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    """编辑目标"""
    user_id = int(get_jwt_identity())
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return error('目标不存在', 404)

    data = json_body()
    if 'title' in data:
        goal.title = data['title'].strip()
    if 'description' in data:
        goal.description = data['description']
    if 'progress' in data:
        progress = data['progress']
        goal.progress = max(0, min(100, progress))
        if goal.progress >= 100:
            goal.status = '已完成'
    if 'status' in data:
        goal.status = data['status']
    if 'start_date' in data:
        try:
            goal.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        except (ValueError, TypeError):
            pass
    if 'end_date' in data:
        try:
            goal.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        except (ValueError, TypeError):
            pass

    db.session.commit()
    return success(goal.to_dict(), '修改成功')


@goals_bp.route('/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    """删除目标"""
    user_id = int(get_jwt_identity())
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return error('目标不存在', 404)
    db.session.delete(goal)
    db.session.commit()
    return success(None, '删除成功')


@goals_bp.route('/<int:goal_id>/progress', methods=['PATCH'])
@jwt_required()
def update_progress(goal_id):
    """更新目标进度"""
    user_id = int(get_jwt_identity())
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return error('目标不存在', 404)

    data = json_body()
    progress = data.get('progress', 0)
    goal.progress = max(0, min(100, progress))
    if goal.progress >= 100:
        goal.status = '已完成'

    db.session.commit()
    return success(goal.to_dict(), '进度更新成功')


@goals_bp.route('/<int:goal_id>/ai-plan', methods=['POST'])
@jwt_required()
def ai_plan(goal_id):
    """AI 根据目标生成执行计划"""
    user_id = int(get_jwt_identity())
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return error('目标不存在', 404)

    try:
        result = chat_json(
            f"为以下目标制定一个分阶段执行计划，返回JSON：{{\"phases\":[{{\"phase\":\"\",\"tasks\":[\"\"]}}]}}\n目标：{goal.title}\n描述：{goal.description or '无'}\n进度：{goal.progress}%",
            "你是目标规划专家，帮助用户制定可执行的阶段性计划。只返回JSON。",
            api_key=get_user_api_key(user_id),
        )
        plan = result.get('phases', []) if result else []
        if not plan:
            plan = [
                {'phase': '准备阶段', 'tasks': ['明确需求', '收集资料', '制定计划']},
                {'phase': '执行阶段', 'tasks': ['推进任务', '跟踪进度', '调整偏差']},
                {'phase': '验收阶段', 'tasks': ['检查质量', '总结经验', '迭代优化']},
            ]
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        plan = [
            {'phase': '准备阶段', 'tasks': ['明确需求', '收集资料', '制定计划']},
            {'phase': '执行阶段', 'tasks': ['推进任务', '跟踪进度', '调整偏差']},
            {'phase': '验收阶段', 'tasks': ['检查质量', '总结经验', '迭代优化']},
        ]
    except Exception:
        plan = [
            {'phase': '准备阶段', 'tasks': ['明确需求', '收集资料', '制定计划']},
            {'phase': '执行阶段', 'tasks': ['推进任务', '跟踪进度', '调整偏差']},
            {'phase': '验收阶段', 'tasks': ['检查质量', '总结经验', '迭代优化']},
        ]

    return success({'goal_title': goal.title, 'plan': plan}, '计划生成完成')
