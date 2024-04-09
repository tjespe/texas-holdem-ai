from sqlitedict import SqliteDict

db = SqliteDict("./db.sqlite", autocommit=False)


def get_value(key: str):
    try:
        return db[key]
    except KeyError:
        return None


def set_value(key: str, value, delay_commit=False):
    db[key] = value
    if not delay_commit:
        commit_everything()


def commit_everything():
    db.commit()
