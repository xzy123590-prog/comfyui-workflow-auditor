import hashlib


def fingerprint(data, enabled=False):
    if type(enabled) is not bool:
        raise ValueError("Invalid fingerprint option.")
    if not enabled:
        return None
    return {"algorithm": "sha256", "user_opt_in": True,
            "value": hashlib.sha256(data).hexdigest()}
