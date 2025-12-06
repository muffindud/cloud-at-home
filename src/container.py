from requests import post, delete, get, put

from src.config import PROXMOX_HOST, PROXMOX_PORT




def create_container():
    node = ...

    response = post(
        url=f"http://{PROXMOX_HOST}:{PROXMOX_PORT}/api2/json/nodes/{node}/lxc",
    )


def delete_container():
    pass


def get_container_info():
    pass


def update_container():
    pass
