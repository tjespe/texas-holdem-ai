import os
from dotenv import load_dotenv

load_dotenv()


def get_env_int(key: str) -> int:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Environment variable {key} not set")
    return int(value)


def get_big_blind():
    try:
        return get_env_int("BIG_BLIND")
    except ValueError:
        print(
            "Warning: BIG_BLIND environment variable not set, using default value of 2"
        )
        return 2
