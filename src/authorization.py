import functools

from flask import request


def get_role(client_ip: str) -> str:
    if client_ip == "127.0.0.1":
        return "admin"
    return None
    ...


def vpn(roles=[]):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            role = get_role(client_ip)

            if roles and role not in roles:
                return {"error": "Unauthorized"}, 403

            return f(*args, **kwargs)

        return wrapper

    return decorator
