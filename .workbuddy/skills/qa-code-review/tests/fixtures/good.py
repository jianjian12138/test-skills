# good.py — 代码评审门禁正例：无阻断项
import logging


def get_user(db, uid):
    # TODO(#123) 增加缓存层避免重复查询
    logger = logging.getLogger(__name__)
    logger.info("fetch user %s", uid)
    return db.fetch(uid)


def render(user):
    if not user:
        return None
    return {"id": user.id, "name": user.name}


def main():
    logger = logging.getLogger(__name__)
    logger.info("start")
    return 0
