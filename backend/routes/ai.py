"""
AI 助手路由 — 接入 DeepSeek API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models import AIRecord, Todo, Note, Goal, User
from extensions import db
from ai_client import chat, chat_json
from routes.helpers import API_KEY_NOT_SET_MSG, get_user_api_key, json_body

ai_bp = Blueprint('ai', __name__)


def success(data=None, message='success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def error(message='error', code=400, data=None):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def save_ai_record(user_id, prompt, result, ai_type='chat'):
    """保存 AI 记录（失败不影响主流程）"""
    try:
        record = AIRecord(user_id=user_id, prompt=prompt, result=str(result), ai_type=ai_type)
        db.session.add(record)
        db.session.commit()
    except Exception:
        db.session.rollback()


SYSTEM_PROMPT = """你是一个专业的个人效率管理助手，帮助用户提升工作效率、管理时间和任务。你的特点是：
1. 给出具体、可操作的建议，不要泛泛而谈
2. 用简洁清晰的格式回复，适当使用编号列表
3. 语气温暖但专业，像一位靠谱的工作伙伴
4. 结合用户的实际使用场景（笔记、待办、日程、番茄钟、目标管理）给出建议"""


@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def ai_chat():
    """AI 对话"""
    user_id = int(get_jwt_identity())
    data = json_body()
    prompt = data.get('prompt', '').strip()

    if not prompt:
        return error('请输入问题', 400)

    try:
        reply = chat(prompt, system_prompt=SYSTEM_PROMPT, api_key=get_user_api_key(user_id))
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        return error(f'AI 服务调用失败: {str(e)}', 500)
    except Exception as e:
        return error(f'AI 服务调用失败: {str(e)}', 500)

    save_ai_record(user_id, prompt, reply, 'chat')
    return success({'reply': reply, 'prompt': prompt}, 'AI 回复完成')


@ai_bp.route('/daily-plan', methods=['POST'])
@jwt_required()
def daily_plan():
    """生成每日计划"""
    user_id = int(get_jwt_identity())
    today = datetime.now()
    day_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][today.weekday()]

    # 获取用户数据作为上下文
    undone = Todo.query.filter_by(user_id=user_id, status='未完成').count()
    today_schedules = Todo.query.filter(
        Todo.user_id == user_id, Todo.status == '未完成',
        Todo.due_date >= today.replace(hour=0, minute=0, second=0),
        Todo.due_date < today.replace(hour=23, minute=59, second=59)
    ).count()

    prompt = f"""请为我生成本日（{today.strftime('%Y-%m-%d')} {day_name}）的每日计划。
我当前有 {undone} 个未完成任务，今天有 {today_schedules} 个截止任务。
请按时间段给出合理的计划安排（从早8点到晚8点），包含专注时间、任务推进、学习充电。
最后给一条实用的效率建议。用 JSON 格式返回：{{"date":"", "day":"", "schedule":[{{"time":"", "task":""}}], "tips":""}}"""

    try:
        result = chat_json(prompt, "你是一个时间管理专家，帮助用户制定高效合理的每日计划。", api_key=get_user_api_key(user_id))
        if not result:
            return error('AI 返回格式异常，请重试', 500)
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        return error(f'AI 服务调用失败: {str(e)}', 500)
    except Exception as e:
        return error(f'AI 服务调用失败: {str(e)}', 500)

    save_ai_record(user_id, '生成每日计划', str(result), 'plan')
    return success({'plan': result}, '计划生成完成')


@ai_bp.route('/task-analysis', methods=['POST'])
@jwt_required()
def task_analysis():
    """分析任务压力"""
    user_id = int(get_jwt_identity())
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    total_todos = Todo.query.filter_by(user_id=user_id).count()
    undone = Todo.query.filter_by(user_id=user_id, status='未完成').count()
    overdue = Todo.query.filter(
        Todo.user_id == user_id, Todo.status == '未完成',
        Todo.due_date.isnot(None), Todo.due_date < today
    ).count()

    # 获取逾期任务详情
    overdue_todos = Todo.query.filter(
        Todo.user_id == user_id, Todo.status == '未完成',
        Todo.due_date.isnot(None), Todo.due_date < today
    ).limit(10).all()
    overdue_titles = [t.title for t in overdue_todos]

    prompt = f"""请分析我的任务压力状况：
- 总任务数：{total_todos}
- 未完成任务：{undone}
- 逾期任务数：{overdue}
- 逾期任务列：{', '.join(overdue_titles) if overdue_titles else '无'}

请给出：
1. 压力等级（高/中/低）
2. 具体分析和建议

用 JSON 格式返回：{{"pressure":"", "total_todos":{total_todos}, "undone":{undone}, "overdue":{overdue}, "advice":""}}"""

    try:
        result = chat_json(prompt, "你是任务管理分析师，客观评估用户的任务压力并给出实用建议。", api_key=get_user_api_key(user_id))
        if not result:
            result = {"pressure": "中", "total_todos": total_todos, "undone": undone, "overdue": overdue,
                      "advice": "建议优先处理逾期任务，合理安排每日工作量。"}
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        result = {"pressure": "中", "total_todos": total_todos, "undone": undone, "overdue": overdue,
                  "advice": "建议优先处理逾期任务，合理安排每日工作量。"}
    except Exception:
        result = {"pressure": "中", "total_todos": total_todos, "undone": undone, "overdue": overdue,
                  "advice": "AI 服务暂时不可用，请稍后重试。"}

    save_ai_record(user_id, '分析任务压力', str(result), 'analysis')
    return success(result, '分析完成')


@ai_bp.route('/summary-today', methods=['POST'])
@jwt_required()
def summary_today():
    """总结今日任务"""
    user_id = int(get_jwt_identity())
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    done_today = Todo.query.filter(
        Todo.user_id == user_id, Todo.status == '已完成',
        Todo.updated_at >= today, Todo.updated_at < tomorrow
    ).all()
    done_titles = [t.title for t in done_today]

    undone_today = Todo.query.filter_by(user_id=user_id, status='未完成').count()
    notes_today = Note.query.filter(
        Note.user_id == user_id, Note.updated_at >= today, Note.updated_at < tomorrow
    ).count()

    prompt = f"""请根据以下数据给我今日工作总结：
- 已完成任务（{len(done_today)}个）：{', '.join(done_titles) if done_titles else '无'}
- 剩余待办：{undone_today} 个
- 更新笔记：{notes_today} 篇

请给一段温暖鼓励的总结语（50字以内），用 JSON 返回：{{"message":""}}"""

    try:
        result = chat_json(prompt, "你是温暖鼓励型的效率伙伴，善于总结和激励。", api_key=get_user_api_key(user_id))
        if not result:
            msg = f'今天完成了 {len(done_today)} 个任务，更新了 {notes_today} 篇笔记，还有 {undone_today} 个待办事项。继续加油！'
            result = {"message": msg}
    except ValueError as e:
        if 'AI_API_KEY_NOT_SET' in str(e):
            return error(API_KEY_NOT_SET_MSG, 400)
        msg = f'今天完成了 {len(done_today)} 个任务，更新了 {notes_today} 篇笔记，还有 {undone_today} 个待办事项。继续加油！'
        result = {"message": msg}
    except Exception:
        msg = f'今天完成了 {len(done_today)} 个任务，更新了 {notes_today} 篇笔记，还有 {undone_today} 个待办事项。继续加油！'
        result = {"message": msg}

    summary = {
        'date': today.strftime('%Y-%m-%d'),
        'completed_tasks': len(done_today),
        'remaining_tasks': undone_today,
        'notes_updated': notes_today,
        'message': result.get('message', ''),
    }

    save_ai_record(user_id, '总结今日任务', str(summary), 'summary')
    return success({'summary': summary}, '总结完成')


@ai_bp.route('/records', methods=['GET'])
@jwt_required()
def get_records():
    """获取 AI 记录"""
    user_id = int(get_jwt_identity())
    ai_type = request.args.get('ai_type', '').strip()

    query = AIRecord.query.filter_by(user_id=user_id)
    if ai_type:
        query = query.filter_by(ai_type=ai_type)

    records = query.order_by(AIRecord.created_at.desc()).limit(50).all()
    return success([r.to_dict() for r in records])
