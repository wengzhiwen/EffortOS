import os
import tempfile
import pytest

from app.services.validate_service import validate_activity_file


def _write_temp(content: str, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
        f.write(content)
        return f.name


def test_valid_tcx():
    path = _write_temp('<?xml version="1.0"?><root/>', ".tcx")
    try:
        ok, msg = validate_activity_file(path)
        assert ok is True
        assert msg == ""
    finally:
        os.unlink(path)


def test_valid_gpx():
    path = _write_temp('<?xml version="1.0"?><root/>', ".gpx")
    try:
        ok, msg = validate_activity_file(path)
        assert ok is True
    finally:
        os.unlink(path)


def test_unsupported_format():
    path = _write_temp('<?xml version="1.0"?><root/>', ".fit")
    try:
        ok, msg = validate_activity_file(path)
        assert ok is False
        assert "不支持" in msg
    finally:
        os.unlink(path)


def test_empty_file():
    path = _write_temp("", ".tcx")
    try:
        ok, msg = validate_activity_file(path)
        assert ok is False
        assert "为空" in msg
    finally:
        os.unlink(path)


def test_nonexistent_file():
    ok, msg = validate_activity_file("/nonexistent/file.tcx")
    assert ok is False
    assert "不存在" in msg


def test_not_xml():
    path = _write_temp("this is not xml", ".tcx")
    try:
        ok, msg = validate_activity_file(path)
        assert ok is False
        assert "XML" in msg
    finally:
        os.unlink(path)
