import os

ALLOWED_EXTENSIONS = {"tcx", "gpx"}


def validate_activity_file(file_path: str) -> tuple[bool, str]:
    """校验运动数据文件。

    返回 (is_valid, error_message)。is_valid=True 时 error_message 为空字符串。
    """
    if not os.path.exists(file_path):
        return False, "文件不存在"

    if os.path.getsize(file_path) == 0:
        return False, "文件为空"

    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件格式: .{ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            header = f.read(100)
    except UnicodeDecodeError:
        return False, "文件编码异常，无法作为 XML 解析"

    if not header.strip().startswith("<?xml"):
        return False, "文件不是有效的 XML 格式"

    return True, ""
