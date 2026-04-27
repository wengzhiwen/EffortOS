from mongoengine import Document


class BaseDocument(Document):
    """所有模型的基类，提供通用字段和方法。"""

    meta = {
        "abstract": True,
    }
