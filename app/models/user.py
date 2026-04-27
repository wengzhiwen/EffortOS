import secrets
from datetime import datetime, timezone

from mongoengine import DateTimeField, EmailField, StringField

from app.models.base import BaseDocument


class User(BaseDocument):
    email = EmailField(required=True, unique=True)
    nickname = StringField(required=True, max_length=50)
    session_token = StringField(unique=True, sparse=True)
    last_login_at = DateTimeField()
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {
        "collection": "users",
        "indexes": ["email", "session_token"],
    }

    def generate_session_token(self) -> str:
        """生成新的 session token。"""
        self.session_token = secrets.token_hex(32)
        self.last_login_at = datetime.now(timezone.utc)
        self.save()
        return self.session_token

    def clear_session_token(self):
        """清除 session token（登出）。"""
        self.session_token = None
        self.save()

    def __str__(self):
        return f"User({self.email})"
