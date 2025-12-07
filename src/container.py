from uuid import uuid4
from json import dumps

from requests import Response, post, delete, get, put
from flask import request

from src.config import PROXMOX_HOST, PROXMOX_PORT, PROXMOX_KEY, NODE
from src.authorization import get_has_access_rule, add_access_rule, remove_resource, get_vmid, get_unique_resource_vmid, set_vmid


DEFAULT_OS_TEMPLATE = "local:vztmpl/ubuntu-25.04-standard_25.04-1.1_amd64.tar.zst"

DATA_TEMPLATE = {
    "vmid": "101",
    "ostemplate": DEFAULT_OS_TEMPLATE,
    "password": "123456",
    "cores": "2",
    "memory": "2048",
    "swap": "512",
    "rootfs": "local-lvm:8",
    "net0": "name=eth0,bridge=vmbr0,firewall=1"
}


def _send_response(message: dict, status_code: int) -> Response:
    response = Response()
    response.status_code = status_code
    response._content = dumps(message).encode('utf-8')
    response.headers['Content-Type'] = 'application/json'
    return response


def send_unauthorized_response() -> Response:
    return _send_response({"error": "Unauthorized"}, 403)


def create_container() -> Response:
    vmid = get_unique_resource_vmid()
    data = DATA_TEMPLATE.copy()
    data["vmid"] = vmid

    response = post(
        url=f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc",
        headers={"Authorization": PROXMOX_KEY},
        data=data,
        verify=False
    )

    uuid = str(uuid4())

    if response.ok:
        add_access_rule(
            client_ip=request.remote_addr,
            resource_uuid=uuid,
            rule="admin"
        )
        set_vmid(uuid, vmid)

    print(response.text)
    print(response.status_code)

    return _send_response({"container": uuid, "status": "created"}, 201)


def delete_container(uuid: str) -> Response:
    if not get_has_access_rule(
        client_ip=request.remote_addr,
        resource_uuid=uuid,
        rule="admin"
    ):
        return send_unauthorized_response()

    vmid = get_vmid(uuid)

    response = delete(
        url=f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc/{vmid}",
        headers={"Authorization": PROXMOX_KEY},
        verify=False
    )

    if response.ok:
        remove_resource(uuid)

    print(response.text)
    print(response.status_code)

    return _send_response({"status": "deleted"}, 200)


def get_container_info(uuid: str) -> Response:
    if not get_has_access_rule(
        client_ip=request.remote_addr,
        resource_uuid=uuid,
        rule="admin"
    ):
        return send_unauthorized_response()

    vmid = get_vmid(uuid)

    response = get(
        url=f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc/{vmid}/status/current",
        headers={"Authorization": PROXMOX_KEY},
        verify=False
    )

    print(response.text)
    print(response.status_code)

    return _send_response({"status": "ok", "data": response.json()}, 200)


def update_container() -> Response:
    pass
