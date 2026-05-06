import hashlib
import os

ALLOWED_EXTENSIONS = {"tcx", "gpx"}
ALLOWED_MIME_TYPES = {"application/xml", "text/xml", "application/gpx+xml"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def validate_activity_file(file_path: str) -> tuple[bool, str]:
    """校验运动数据文件。

    检查项：存在性、大小、扩展名、XML 头、无二进制内容。
    返回 (is_valid, error_message)。
    """
    if not os.path.exists(file_path):
        return False, "文件不存在"

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return False, "文件为空"
    if file_size > MAX_FILE_SIZE:
        return False, f"文件过大（{file_size / 1024 / 1024:.0f}MB），上限 50MB"

    # 扩展名检查
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件格式: .{ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}"

    # 二进制内容检测：检查文件头是否为合法的文本/XML
    try:
        with open(file_path, "rb") as f:
            raw_header = f.read(512)
    except OSError:
        return False, "无法读取文件"

    # 检查是否包含 null 字节（二进制文件特征）
    if b"\x00" in raw_header:
        return False, "文件包含二进制内容，不是有效的运动数据文件"

    # XML 声明检查
    try:
        header = raw_header.decode("utf-8").strip()
    except UnicodeDecodeError:
        return False, "文件编码异常，无法作为 XML 解析"

    if not header.startswith("<?xml"):
        return False, "文件不是有效的 XML 格式"

    return True, ""


def compute_file_checksum(file_path: str) -> str:
    """计算文件内容的 SHA-256 校验和。"""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
