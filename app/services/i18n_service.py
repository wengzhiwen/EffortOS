import json
import os

from flask import g, request

_TRANSLATIONS = {}
_SUPPORTED_LANGS = ["zh_CN", "en", "zh_TW", "ja"]
_DEFAULT_LANG = "zh_CN"
_LANG_DISPLAY = {
    "zh_CN": "中文",
    "en": "English",
    "zh_TW": "繁體中文",
    "ja": "日本語",
}

_LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "locales")


def _load_translations():
    global _TRANSLATIONS
    for lang in _SUPPORTED_LANGS:
        path = os.path.join(_LOCALES_DIR, f"{lang}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                _TRANSLATIONS[lang] = json.load(f)


def detect_language():
    """Detect language from: cookie → Accept-Language → default."""
    lang = request.cookies.get("lang")
    if lang in _SUPPORTED_LANGS:
        return lang
    accept = request.headers.get("Accept-Language", "")
    for part in accept.split(","):
        code = part.split(";")[0].strip().lower()
        if code.startswith("zh"):
            if "tw" in code or "hant" in code:
                return "zh_TW"
            return "zh_CN"
        elif code.startswith("ja"):
            return "ja"
        elif code.startswith("en"):
            return "en"
    return _DEFAULT_LANG


def t(key, lang=None, **kwargs):
    """Translate a key using dot-notation (e.g. 'nav.dashboard')."""
    if lang is None:
        lang = getattr(g, "lang", _DEFAULT_LANG)
    value = _get_value(key, lang)
    if value is None:
        value = _get_value(key, _DEFAULT_LANG)
    if value is None:
        return key
    if kwargs and isinstance(value, str):
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError):
            return value
    return value


def _get_value(key, lang):
    dict_obj = _TRANSLATIONS.get(lang, {})
    for part in key.split("."):
        if isinstance(dict_obj, dict):
            dict_obj = dict_obj.get(part)
        else:
            return None
    return dict_obj


def get_translations_json(lang):
    """Return the full translation dict for a language."""
    return _TRANSLATIONS.get(lang, {})


def init_app(app):
    """Register i18n hooks on a Flask app."""
    _load_translations()

    @app.before_request
    def set_language():
        g.lang = detect_language()

    @app.context_processor
    def inject_i18n():
        lang = getattr(g, "lang", _DEFAULT_LANG)
        return {
            "t": t,
            "current_lang": lang,
            "supported_langs": _SUPPORTED_LANGS,
            "lang_display": _LANG_DISPLAY,
            "translations_json": json.dumps(get_translations_json(lang), ensure_ascii=False),
        }
