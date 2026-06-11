"""
Flask 应用入口
创建应用、注册蓝图、初始化扩展、创建数据库表
"""
from flask import Flask, jsonify, request
from config import Config
from extensions import db, jwt, cors


def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', [])}},
        supports_credentials=True,
    )

    # JWT 错误处理器 — 所有未授权请求返回 401，前端弹出登录弹窗
    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        return jsonify({'code': 401, 'message': '请先登录', 'data': None}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'code': 401, 'message': '登录已过期，请重新登录', 'data': None}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({'code': 401, 'message': '登录凭证无效', 'data': None}), 401

    # 注册蓝图
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.notes import notes_bp
    from routes.todos import todos_bp
    from routes.schedules import schedules_bp
    from routes.focus import focus_bp
    from routes.goals import goals_bp
    from routes.collections import collections_bp
    from routes.ai import ai_bp
    from routes.achievements import achievements_bp
    from routes.search import search_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(notes_bp, url_prefix='/api/notes')
    app.register_blueprint(todos_bp, url_prefix='/api/todos')
    app.register_blueprint(schedules_bp, url_prefix='/api/schedules')
    app.register_blueprint(focus_bp, url_prefix='/api/focus')
    app.register_blueprint(goals_bp, url_prefix='/api/goals')
    app.register_blueprint(collections_bp, url_prefix='/api/collections')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(achievements_bp, url_prefix='/api/achievements')
    app.register_blueprint(search_bp, url_prefix='/api/search')

    # SQLite 外键支持
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if not app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            return
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    # 创建数据库表
    with app.app_context():
        from models import User, Note, Todo, Schedule, FocusRecord, Goal, Collection, AIRecord
        if app.config.get('AUTO_CREATE_TABLES', True):
            db.create_all()

    # 健康检查
    @app.route('/api/health')
    def health():
        return {'code': 200, 'message': 'OK', 'data': None}

    return app


app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
