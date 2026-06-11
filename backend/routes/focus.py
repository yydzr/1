"""
番茄钟专注路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models import FocusRecord
from extensions import db
from routes.helpers import json_body

focus_bp = Blueprint('focus', __name__)


def success(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def error(message='error', code=400, data=None):
    return jsonify({'code': code, 'message': message, 'data': data}), code


@focus_bp.route('/records', methods=['GET'])
@jwt_required()
def get_records():
    """查询专注记录"""
    user_id = int(get_jwt_identity())
    records = FocusRecord.query.filter_by(user_id=user_id).order_by(FocusRecord.created_at.desc()).limit(100).all()
    return success([r.to_dict() for r in records])


@focus_bp.route('/records', methods=['POST'])
@jwt_required()
def create_record():
    """保存专注记录"""
    user_id = int(get_jwt_identity())
    data = json_body()

    duration = data.get('duration', 0)
    if duration <= 0:
        return error('专注时长必须大于 0', 400)

    started_at = None
    if data.get('started_at'):
        try:
            started_at = datetime.strptime(data['started_at'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            pass

    ended_at = datetime.now()
    if data.get('ended_at'):
        try:
            ended_at = datetime.strptime(data['ended_at'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            pass

    record = FocusRecord(
        user_id=user_id,
        duration=duration,
        focus_type=data.get('focus_type', '番茄钟'),
        started_at=started_at,
        ended_at=ended_at,
    )
    db.session.add(record)
    db.session.commit()
    return success(record.to_dict(), '保存成功')


@focus_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """专注统计"""
    user_id = int(get_jwt_identity())
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    # 今日专注
    today_focus = db.session.query(db.func.coalesce(db.func.sum(FocusRecord.duration), 0)).filter(
        FocusRecord.user_id == user_id,
        FocusRecord.created_at >= today,
        FocusRecord.created_at < tomorrow
    ).scalar()

    # 累计专注
    total_focus = db.session.query(db.func.coalesce(db.func.sum(FocusRecord.duration), 0)).filter(
        FocusRecord.user_id == user_id
    ).scalar()

    # 今日记录数
    today_count = FocusRecord.query.filter(
        FocusRecord.user_id == user_id,
        FocusRecord.created_at >= today,
        FocusRecord.created_at < tomorrow
    ).count()

    return success({
        'today_focus': int(today_focus or 0),
        'total_focus': int(total_focus or 0),
        'today_count': today_count,
    })


@focus_bp.route('/charts', methods=['GET'])
@jwt_required()
def get_charts():
    """专注趋势图"""
    user_id = int(get_jwt_identity())
    days = []
    durations = []

    for i in range(6, -1, -1):
        target_date = datetime.now().date() - timedelta(days=i)
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        day_focus = db.session.query(db.func.coalesce(db.func.sum(FocusRecord.duration), 0)).filter(
            FocusRecord.user_id == user_id,
            FocusRecord.created_at >= day_start,
            FocusRecord.created_at < day_end
        ).scalar()
        days.append(target_date.strftime('%m-%d'))
        durations.append(int(day_focus or 0))

    return success({'days': days, 'durations': durations})
