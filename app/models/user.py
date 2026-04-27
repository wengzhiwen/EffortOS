from datetime import datetime, timezone

from mongoengine import DateTimeField, EmailField, StringField

from app.models.base import BaseDocument


class User(BaseDocument):
    email = EmailField(required=True, unique=True)
    nickname = StringField(required=True, max_length=50)
    password_hash = StringField()  # 预留，当前版本可能使用邮箱验证码登录
    session_token = StringField()
    last_login_at = DateTimeField()
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {
        "collection": "users",
    }

    def __str__(self):
        return f"User({self.email})"
