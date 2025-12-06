from dotenv import dotenv_values

config = dotenv_values(".env")

REMOTE_HOST = config["REMOTE_HOST"]
REMOTE_PORT = config["REMOTE_PORT"]
EASY_RSA_PATH = config["EASY_RSA_PATH"]
PROXMOX_HOST = config["PROXMOX_HOST"]
PROXMOX_PORT = config["PROXMOX_PORT"]
