"""
日程管理路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models import Schedule
from extensions import db
from routes.helpers import json_body, paged_payload, paginate, wants_paged_response

schedules_bp = Blueprint('schedules', __name__)


def success(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def error(message='error', code=400, data=None):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def parse_datetime(s):
    """解析日期字符串"""
    if not s:
        return None
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            continue
    return None


@schedules_bp.route('', methods=['GET'])
@jwt_required()
def get_schedules():
    """获取日程列表"""
    user_id = int(get_jwt_identity())
    date_str = request.args.get('date', '').strip()

    query = Schedule.query.filter_by(user_id=user_id)
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            day_start = datetime.combine(target_date, datetime.min.time())
            day_end = day_start + timedelta(days=1)
            query = query.filter(
                Schedule.start_time >= day_start,
                Schedule.start_time < day_end
            )
        except (ValueError, TypeError):
            pass

    query = query.order_by(Schedule.start_time.asc())
    if wants_paged_response():
        return success(paged_payload(query, lambda s: s.to_dict()))
    schedules = paginate(query).all()
    return success([s.to_dict() for s in schedules])


@schedules_bp.route('/dates', methods=['GET'])
@jwt_required()
def get_schedule_dates():
    """获取有日程的日期索引，用于日历标记"""
    user_id = int(get_jwt_identity())
    schedules = Schedule.query.filter_by(user_id=user_id).with_entities(
        Schedule.start_time,
        Schedule.end_time,
    ).all()

    starts = set()
    ends = set()
    for schedule in schedules:
        if schedule.start_time:
            starts.add(schedule.start_time.date().isoformat())
        if schedule.end_time and schedule.start_time and schedule.end_time.date() != schedule.start_time.date():
            ends.add(schedule.end_time.date().isoformat())

    return success({
        'starts': sorted(starts),
        'ends': sorted(ends),
    })


@schedules_bp.route('', methods=['POST'])
@jwt_required()
def create_schedule():
    """新增日程"""
    user_id = int(get_jwt_identity())
    data = json_body()

    title = data.get('title', '').strip()
    if not title:
        return error('日程标题不能为空', 400)

    start_time = parse_datetime(data.get('start_time'))
    end_time = parse_datetime(data.get('end_time'))
    if not start_time or not end_time:
        return error('开始时间和结束时间不能为空', 400)
    if end_time <= start_time:
        return error('结束时间必须晚于开始时间', 400)

    schedule = Schedule(
        user_id=user_id,
        title=title,
        description=data.get('description', ''),
        location=data.get('location', ''),
        start_time=start_time,
        end_time=end_time,
        color=data.get('color', '#409EFF'),
    )
    db.session.add(schedule)
    db.session.commit()
    return success(schedule.to_dict(), '创建成功')


@schedules_bp.route('/<int:schedule_id>', methods=['GET'])
@jwt_required()
def get_schedule(schedule_id):
    """查看日程详情"""
    user_id = int(get_jwt_identity())
    schedule = Schedule.query.filter_by(id=schedule_id, user_id=user_id).first()
    if not schedule:
        return error('日程不存在', 404)
    return success(schedule.to_dict())


@schedules_bp.route('/<int:schedule_id>', methods=['PUT'])
@jwt_required()
def update_schedule(schedule_id):
    """编辑日程"""
    user_id = int(get_jwt_identity())
    schedule = Schedule.query.filter_by(id=schedule_id, user_id=user_id).first()
    if not schedule:
        return error('日程不存在', 404)

    data = json_body()
    if 'title' in data:
        schedule.title = data['title'].strip()
    if 'description' in data:
        schedule.description = data['description']
    if 'location' in data:
        schedule.location = data['location']
    if 'start_time' in data:
        st = parse_datetime(data['start_time'])
        if st:
            schedule.start_time = st
    if 'end_time' in data:
        et = parse_datetime(data['end_time'])
        if et:
            schedule.end_time = et
    if schedule.end_time <= schedule.start_time:
        return error('结束时间必须晚于开始时间', 400)
    if 'color' in data:
        schedule.color = data['color']

    db.session.commit()
    return success(schedule.to_dict(), '修改成功')


@schedules_bp.route('/<int:schedule_id>', methods=['DELETE'])
@jwt_required()
def delete_schedule(schedule_id):
    """删除日程"""
    user_id = int(get_jwt_identity())
    schedule = Schedule.query.filter_by(id=schedule_id, user_id=user_id).first()
    if not schedule:
        return error('日程不存在', 404)
    db.session.delete(schedule)
    db.session.commit()
    return success(None, '删除成功')


@schedules_bp.route('/today', methods=['GET'])
@jwt_required()
def today_schedules():
    """获取今日日程"""
    user_id = int(get_jwt_identity())
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    schedules = Schedule.query.filter(
        Schedule.user_id == user_id,
        Schedule.start_time >= today,
        Schedule.start_time < tomorrow
    ).order_by(Schedule.start_time.asc()).all()
    return success([s.to_dict() for s in schedules])


@schedules_bp.route('/week', methods=['GET'])
@jwt_required()
def week_schedules():
    """获取本周日程"""
    user_id = int(get_jwt_identity())
    now = datetime.now()
    monday = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
    sunday = monday + timedelta(days=7)

    schedules = Schedule.query.filter(
        Schedule.user_id == user_id,
        Schedule.start_time >= monday,
        Schedule.start_time < sunday
    ).order_by(Schedule.start_time.asc()).all()
    return success([s.to_dict() for s in schedules])
