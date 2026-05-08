import secrets
import string
from datetime import datetime, timezone

from mongoengine import DateTimeField, StringField

from app.models.base import BaseDocument


class VerificationCode(BaseDocument):
    """邮箱验证码，用于无密码登录。"""

    email = StringField(required=True)
    code = StringField(required=True, max_length=6)
    used_at = DateTimeField()
    created_at = DateTimeField(default=lambda: datetime.utcnow())

    meta = {
        "collection": "verification_codes",
        "indexes": ["email", "-created_at"],
    }

    @classmethod
    def create_for_email(cls, email: str, expiry_minutes: int = 10) -> "VerificationCode":
        """为邮箱生成验证码，同时使旧验证码失效。"""
        # 使旧的未使用验证码失效
        for vc in cls.objects(email=email, used_at=None):
            vc.used_at = datetime.now(timezone.utc)
            vc.save()

        code = "".join(secrets.choice(string.digits) for _ in range(6))
        vc = cls(email=email.lower().strip(), code=code)
        vc.save()
        return vc

    def is_valid(self, expiry_minutes: int = 10) -> bool:
        """检查验证码是否有效（未使用且未过期）。"""
        if self.used_at is not None:
            return False
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age < expiry_minutes * 60

    def mark_used(self):
        """标记验证码为已使用。"""
        self.used_at = datetime.now(timezone.utc)
        self.save()
