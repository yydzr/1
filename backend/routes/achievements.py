"""
成就系统路由
根据用户现有数据实时计算成就解锁状态与进度
"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from extensions import db
from models import Collection, FocusRecord, Goal, Note, Schedule, Todo

achievements_bp = Blueprint('achievements', __name__)


def success(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def _sum_focus(user_id):
    return db.session.query(db.func.coalesce(db.func.sum(FocusRecord.duration), 0)).filter(
        FocusRecord.user_id == user_id
    ).scalar()


def _focus_streak(user_id):
    records = FocusRecord.query.filter_by(user_id=user_id).with_entities(FocusRecord.created_at).all()
    focus_days = {
        row.created_at.date()
        for row in records
        if row.created_at
    }
    if not focus_days:
        return 0

    streak = 0
    cursor = datetime.now().date()
    while cursor in focus_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _achievement(code, title, description, category, value, target):
    progress = 100 if target <= 0 else min(100, int((value / target) * 100))
    return {
        'code': code,
        'title': title,
        'description': description,
        'category': category,
        'value': int(value or 0),
        'target': int(target),
        'progress': progress,
        'unlocked': value >= target,
    }


@achievements_bp.route('', methods=['GET'])
@jwt_required()
def list_achievements():
    """获取用户成就进度"""
    user_id = int(get_jwt_identity())

    notes_count = Note.query.filter_by(user_id=user_id, is_archived=False).count()
    todos_created = Todo.query.filter_by(user_id=user_id).count()
    todos_done = Todo.query.filter_by(user_id=user_id, status='已完成').count()
    total_focus = int(_sum_focus(user_id) or 0)
    focus_sessions = FocusRecord.query.filter_by(user_id=user_id).count()
    focus_streak = _focus_streak(user_id)
    goals_count = Goal.query.filter_by(user_id=user_id).count()
    goals_done = Goal.query.filter(
        Goal.user_id == user_id,
        or_(Goal.status == '已完成', Goal.progress >= 100),
    ).count()
    collections_count = Collection.query.filter_by(user_id=user_id).count()
    schedules_count = Schedule.query.filter_by(user_id=user_id).count()

    achievements = [
        _achievement('first_note', '灵感起笔', '创建第一篇笔记', '笔记', notes_count, 1),
        _achievement('note_collector', '笔记收藏家', '累计创建 10 篇笔记', '笔记', notes_count, 10),
        _achievement('task_first_done', '任务破冰', '完成第一个待办任务', '待办', todos_done, 1),
        _achievement('task_master', '执行力达人', '累计完成 10 个待办任务', '待办', todos_done, 10),
        _achievement('task_planner', '计划启动器', '累计创建 10 个待办任务', '待办', todos_created, 10),
        _achievement('focus_beginner', '进入心流', '累计专注 25 分钟', '专注', total_focus, 25),
        _achievement('focus_runner', '稳定专注', '累计完成 10 次专注记录', '专注', focus_sessions, 10),
        _achievement('focus_streak_3', '连续专注', '连续 3 天留下专注记录', '专注', focus_streak, 3),
        _achievement('goal_setter', '目标上墙', '创建第一个目标', '目标', goals_count, 1),
        _achievement('goal_finisher', '目标达成', '完成第一个目标', '目标', goals_done, 1),
        _achievement('knowledge_keeper', '知识仓库', '累计收藏 5 条知识资源', '收藏', collections_count, 5),
        _achievement('schedule_keeper', '日程管家', '累计创建 5 条日程', '日程', schedules_count, 5),
    ]

    unlocked = sum(1 for item in achievements if item['unlocked'])
    return success({
        'items': achievements,
        'summary': {
            'total': len(achievements),
            'unlocked': unlocked,
            'locked': len(achievements) - unlocked,
            'progress': round((unlocked / len(achievements)) * 100, 1) if achievements else 0,
            'focus_streak': focus_streak,
        },
    })
