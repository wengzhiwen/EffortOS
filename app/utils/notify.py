import logging
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

BARK_URL = "https://api.day.app/eTuZXiPkB25TnukYbXuon5"


def bark_notify(title: str, body: str):
    """通过 Bark 推送通知。"""
    try:
        url = f"{BARK_URL}/{urllib.parse.quote(title)}/{urllib.parse.quote(body)}"
        urllib.request.urlopen(url, timeout=5)
    except Exception:
        logger.debug("Bark 通知发送失败", exc_info=True)
