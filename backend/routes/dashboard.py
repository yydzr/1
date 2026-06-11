"""
首页数据看板路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models import Note, Todo, Schedule, FocusRecord, Goal
from extensions import db

dashboard_bp = Blueprint('dashboard', __name__)


def success(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def stats():
    """首页统计数据"""
    user_id = int(get_jwt_identity())
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    notes_count = Note.query.filter_by(user_id=user_id, is_archived=False).count()
    todos_total = Todo.query.filter_by(user_id=user_id).count()
    todos_done = Todo.query.filter_by(user_id=user_id, status='已完成').count()
    todos_undone = Todo.query.filter_by(user_id=user_id, status='未完成').count()
    todos_overdue = Todo.query.filter(
        Todo.user_id == user_id,
        Todo.status == '未完成',
        Todo.due_date.isnot(None),
        Todo.due_date < today
    ).count()
    today_schedules = Schedule.query.filter(
        Schedule.user_id == user_id,
        Schedule.start_time >= today,
        Schedule.start_time < tomorrow
    ).count()

    # 专注时长统计
    today_focus = db.session.query(db.func.coalesce(db.func.sum(FocusRecord.duration), 0)).filter(
        FocusRecord.user_id == user_id,
        FocusRecord.created_at >= today,
        FocusRecord.created_at < tomorrow
    ).scalar()
    total_focus = db.session.query(db.func.coalesce(db.func.sum(FocusRecord.duration), 0)).filter(
        FocusRecord.user_id == user_id
    ).scalar()

    # 目标统计
    goals_count = Goal.query.filter_by(user_id=user_id).count()
    avg_progress = db.session.query(db.func.coalesce(db.func.avg(Goal.progress), 0)).filter(
        Goal.user_id == user_id
    ).scalar()

    # 最近笔记
    recent_notes = Note.query.filter_by(user_id=user_id).order_by(Note.updated_at.desc()).limit(5).all()

    # 今日待办
    today_todos = Todo.query.filter(
        Todo.user_id == user_id,
        Todo.status == '未完成',
        Todo.due_date.isnot(None),
        Todo.due_date >= today,
        Todo.due_date < tomorrow
    ).order_by(Todo.priority.desc(), Todo.created_at.desc()).limit(5).all()

    # 今日日程
    today_schedule_list = Schedule.query.filter(
        Schedule.user_id == user_id,
        Schedule.start_time >= today,
        Schedule.start_time < tomorrow
    ).order_by(Schedule.start_time.asc()).all()

    return success({
        'notes_count': notes_count,
        'todos_total': todos_total,
        'todos_done': todos_done,
        'todos_undone': todos_undone,
        'todos_overdue': todos_overdue,
        'today_schedules': today_schedules,
        'today_focus': int(today_focus or 0),
        'total_focus': int(total_focus or 0),
        'goals_count': goals_count,
        'avg_progress': round(float(avg_progress or 0), 1),
        'recent_notes': [n.to_dict() for n in recent_notes],
        'today_todos': [t.to_dict() for t in today_todos],
        'today_schedule_list': [s.to_dict() for s in today_schedule_list],
    })


@dashboard_bp.route('/charts', methods=['GET'])
@jwt_required()
def charts():
    """首页图表数据"""
    user_id = int(get_jwt_identity())

    # 最近 7 天任务完成趋势
    days = []
    completed_list = []
    for i in range(6, -1, -1):
        target_date = datetime.now().date() - timedelta(days=i)
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        done_count = Todo.query.filter(
            Todo.user_id == user_id,
            Todo.status == '已完成',
            Todo.updated_at >= day_start,
            Todo.updated_at < day_end
        ).count()
        days.append(target_date.strftime('%m-%d'))
        completed_list.append(done_count)

    # 任务状态分布
    total_done = Todo.query.filter_by(user_id=user_id, status='已完成').count()
    total_undone = Todo.query.filter_by(user_id=user_id, status='未完成').count()

    return success({
        'trend': {
            'days': days,
            'completed': completed_list,
        },
        'distribution': [
            {'name': '已完成', 'value': total_done},
            {'name': '未完成', 'value': total_undone},
        ],
    })
