DEFAULT_MAX_BYTES = 1_048_576
MAX_BYTES = 16_777_216
DEFAULT_MAX_DEPTH = 64
MAX_DEPTH = 128


def validate_limit(value, maximum):
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError("Invalid limit.")
    return value

DEFAULT_MAX_NODES = 10_000
HARD_MAX_NODES = 100_000
DEFAULT_MAX_LINKS = 50_000
HARD_MAX_LINKS = 500_000
