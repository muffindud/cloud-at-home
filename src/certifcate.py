from subprocess import run

from src.config import REMOTE_HOST, REMOTE_PORT, EASY_RSA_PATH


def create_cert(cn: str, req: str) -> str:
    config = open("template.ovpn", "r").read()

    with open(f"{EASY_RSA_PATH}/pki/reqs/{cn}.req", "x") as f:
        f.write(req)

    run([f"{EASY_RSA_PATH}/easyrsa", "--batch", "sign-req", "client", cn], cwd=EASY_RSA_PATH)

    inline = open(f"{EASY_RSA_PATH}/pki/inline/private/{cn}.inline", "r").read()

    config = config.replace("%REMOTE_HOST%", REMOTE_HOST)
    config = config.replace("%REMOTE_PORT%", REMOTE_PORT)
    config = config.replace("%INLINE%", inline)

    path = f"./temp/{cn}.ovpn"

    with open(path, "+w") as f:
        f.write(config)

    return path
