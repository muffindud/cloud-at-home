import functools
import os
from json import loads, dumps

from flask import request


if not os.path.exists("data/role_mappings.json"):
    with open("data/role_mappings.json", "w") as f:
        f.write(dumps({}))

if not os.path.exists("data/resource_mappings.json"):
    with open("data/resource_mappings.json", "w") as f:
        f.write(dumps({}))


ROLE_MAPPINGS: dict = loads(open("data/role_mappings.json", "r").read())
RESOURCE_MAPPINGS: dict = loads(open("data/resource_mappings.json", "r").read())


def set_role(client_ip: str, role: str) -> None:
    ROLE_MAPPINGS[client_ip] = role
    with open("data/role_mappings.json", "w") as f:
        f.write(dumps(ROLE_MAPPINGS))


def get_role(client_ip: str) -> str:
    return ROLE_MAPPINGS.get(client_ip)


def get_has_access_rules(client_ip: str, resource_uuid: str, rules: list[str]) -> bool:
    resource_rules = RESOURCE_MAPPINGS.get(resource_uuid, {})
    client_rules = resource_rules.get(client_ip, [])

    for rule in rules:
        if rule in client_rules:
            return True

    return False


def add_access_rule(client_ip: str, resource_uuid: str, rule: str) -> None:
    if resource_uuid not in RESOURCE_MAPPINGS:
        RESOURCE_MAPPINGS[resource_uuid] = {}

    if client_ip not in RESOURCE_MAPPINGS[resource_uuid]:
        RESOURCE_MAPPINGS[resource_uuid][client_ip] = []

    if rule not in RESOURCE_MAPPINGS[resource_uuid][client_ip]:
        RESOURCE_MAPPINGS[resource_uuid][client_ip].append(rule)

    with open("data/resource_mappings.json", "w") as f:
        f.write(dumps(RESOURCE_MAPPINGS))


def remove_access_rule(client_ip: str, resource_uuid: str, rule: str) -> None:
    if resource_uuid in RESOURCE_MAPPINGS:
        if client_ip in RESOURCE_MAPPINGS[resource_uuid]:
            if rule in RESOURCE_MAPPINGS[resource_uuid][client_ip]:
                RESOURCE_MAPPINGS[resource_uuid][client_ip].remove(rule)

    with open("data/resource_mappings.json", "w") as f:
        f.write(dumps(RESOURCE_MAPPINGS))


def get_containers_info() -> dict:
    containers_info = []

    for resource_uuid, access_info in RESOURCE_MAPPINGS.items():
        vmid = get_vmid(resource_uuid)
        access = access_info.get(request.remote_addr, [])

        containers_info.append({
            "uuid": resource_uuid,
            "access_rules": access
        })

    return containers_info


def set_vmid(uuid: str, vmid: str) -> None:
    if uuid not in RESOURCE_MAPPINGS:
        RESOURCE_MAPPINGS[uuid] = {}

    RESOURCE_MAPPINGS[uuid]["vmid"] = vmid

    with open("data/resource_mappings.json", "w") as f:
        f.write(dumps(RESOURCE_MAPPINGS))


def get_vmid(uuid: str) -> str:
    return RESOURCE_MAPPINGS.get(uuid, {}).get("vmid")


def get_unique_resource_vmid() -> str:
    # TODO: Generate it based of remote_addr

    existing_vmids = {info.get("vmid") for info in RESOURCE_MAPPINGS.values() if "vmid" in info}
    vmid = 200

    while str(vmid) in existing_vmids:
        vmid += 1

    return str(vmid)


def remove_resource(resource_uuid: str) -> None:
    if resource_uuid in RESOURCE_MAPPINGS:
        del RESOURCE_MAPPINGS[resource_uuid]

    with open("data/resource_mappings.json", "w") as f:
        f.write(dumps(RESOURCE_MAPPINGS))


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



def iam(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr

        # TODO: implement IAM logic
        ...

        return f(*args, **kwargs)

    return wrapper
