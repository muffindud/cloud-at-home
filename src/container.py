from uuid import uuid4
from json import dumps
from time import sleep

from requests import Response, post, delete, get, put
from flask import request

from src.config import PROXMOX_HOST, PROXMOX_PORT, PROXMOX_KEY, NODE
from src.authorization import get_has_access_rules, add_access_rule, remove_resource, get_vmid, get_unique_resource_vmid, set_vmid, get_containers_info


DEFAULT_OS_TEMPLATE = "local:vztmpl/ubuntu-25.04-standard_25.04-1.1_amd64.tar.zst"

DATA_TEMPLATE = {
    "ostemplate": DEFAULT_OS_TEMPLATE,
    "features": "nesting=1",
    "swap": "512",
    "net0": "name=eth0,bridge=vmbr0,firewall=1,ip=dhcp,ip6=dhcp,type=veth",
}

REQUEST_SPEC = {
    "headers": {"Authorization": PROXMOX_KEY},
    "verify": False
}


def _send_response(message: dict, status_code: int) -> Response:
    response = Response()
    response.status_code = status_code
    response._content = dumps(message).encode('utf-8')
    response.headers['Content-Type'] = 'application/json'
    return response


def send_unauthorized_response() -> Response:
    return _send_response({"error": "Unauthorized"}, 403)


def _get_info_container(uuid: str) -> dict:
    vmid = get_vmid(uuid)

    current_response = get(
        url=f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc/{vmid}/status/current",
        **REQUEST_SPEC
    )

    print(current_response.text)
    print(current_response.status_code)

    network = get(
        url=f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc/{vmid}/interfaces",
        **REQUEST_SPEC
    )

    print(network.text)
    print(network.status_code)

    ip_address = None
    network_body = network.json()
    if network_body.get("data") is not None:
        for interface in network_body.get("data"):
            if interface.get("name") == "eth0":
                for ip_info in interface.get("ip-addresses", []):
                    if ip_info.get("ip-address-type") == "inet":
                        ip_address = ip_info.get("ip-address")
                        break

    config_response = get(
        f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc/{vmid}/config",
        **REQUEST_SPEC
    )

    print(config_response.text)
    print(config_response.status_code)

    config_data = config_response.json().get("data")

    retry = 0
    while retry < 3:
        retry += 1
        config_response = get(
            f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc/{vmid}/config",
            **REQUEST_SPEC
        )

        print(config_response.text)
        print(config_response.status_code)

        config_data = config_response.json().get("data")

        if config_data.get("lock") is None:
            break

        sleep(2)

    client_response = {
        "status": current_response.json().get("data").get("status"),
        "ip": ip_address,
        "uuid": uuid,
        "config": {
            "ostype": config_data.get("ostype"),
            "rootfs": config_data.get("rootfs"),
            "memory": config_data.get("memory"),
            "cores": config_data.get("cores")
        }
    }

    return client_response


def create_container() -> Response:
    data = request.json or {}
    for key in ["cores", "ram", "rootfs", "ssh-public-key", "password"]:
        if key not in data:
            return _send_response({"error": f"{key} is required"}, 400)

    vmid = get_unique_resource_vmid()
    container = DATA_TEMPLATE.copy()
    container["vmid"] = vmid

    container["cores"] = str(data["cores"])
    container["memory"] = str(data["ram"])
    container["rootfs"] = f"local-lvm:{data['rootfs']}"
    container["ssh-public-keys"] = data["ssh-public-key"]

    response = post(
        url=f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc",
        **REQUEST_SPEC,
        data=container
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

    return _send_response(_get_info_container(uuid), 201)


def delete_container(uuid: str) -> Response:
    if not get_has_access_rules(
        client_ip=request.remote_addr,
        resource_uuid=uuid,
        rules=["admin"]
    ):
        return send_unauthorized_response()

    vmid = get_vmid(uuid)

    response = delete(
        url=f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc/{vmid}",
        **REQUEST_SPEC
    )

    print(response.text)
    print(response.status_code)

    if response.ok:
        remove_resource(uuid)

    return _send_response({"status": "deleted"}, 200)


def get_container_info(uuid: str) -> Response:
    if not get_has_access_rules(
        client_ip=request.remote_addr,
        resource_uuid=uuid,
        rules=["admin", "maintain", "read"]
    ):
        return send_unauthorized_response()

    return _send_response(_get_info_container(uuid), 200)

def update_container(uuid: str) -> Response:
    if not get_has_access_rules(
        client_ip=request.remote_addr,
        resource_uuid=uuid,
        rules=["admin", "maintain"]
    ):
        return send_unauthorized_response()

    vmid = get_vmid(uuid)

    data: dict = request.json or {}

    if not "status" in data or data["status"] not in ["start", "stop", "reboot"]:
        return _send_response({"error": "Status must be one of start, stop, reboot"}, 400)

    if data["status"] == "start":
        response = post(
            url=f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc/{vmid}/status/start",
            **REQUEST_SPEC
        )
    elif data["status"] == "stop":
        response = post(
            url=f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc/{vmid}/status/stop",
            **REQUEST_SPEC
        )
    elif data["status"] == "reboot":
        response = post(
            url=f"https://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{NODE}/lxc/{vmid}/status/reboot",
            **REQUEST_SPEC
        )

    print(response.text)
    print(response.status_code)

    return _send_response({"status": "updated"}, 200)


def get_containers() -> Response:
    containers = get_containers_info()
    return _send_response({"containers": containers}, 200)
