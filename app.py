from subprocess import run

from dotenv import dotenv_values
from OpenSSL import crypto
from flask import Flask, request


app = Flask(__name__)
config = dotenv_values(".env")

REMOTE_HOST = config["REMOTE_HOST"]
REMOTE_PORT = config["REMOTE_PORT"]

CERT_PATH = config["CERT_PATH"]
CA_PATH = config["CA_PATH"]
TC_PATH = config["TC_PATH"]


def crete_cert(cn: str, req: str) -> str:
    with open(f"/etc/openvpn/server/easy-rsa/pki/reqs/{cn}.req", "w") as f:
        f.write(req)

    run(["/etc/openvpn/server/easy-rsa/easyrsa", "--batch", "sign-req","client", cn], cwd="/etc/openvpn/server/easy-rsa")

    inline = open(f"/etc/openvpn/server/easy-rsa/pki/inline/private/{cn}.inline", "r").read()

    return inline


def create_config(cn: str, req: str) -> str:
    config = open("template.ovpn", "r").read()
    inline = crete_cert(cn, req)

    # Replace placeholders in the template
    config = config.replace("%REMOTE_HOST%", REMOTE_HOST)
    config = config.replace("%REMOTE_PORT%", REMOTE_PORT)
    config = config.replace("%INLINE%", inline)

    return config


@app.route("/generate", methods=["POST"])
def generate_vpn_config():
    data = request.get_json()

    if not "key" in data:
        return {"error": "Missing 'key' in request body"}, 400
    if not "cn" in data:
        return {"error": "Missing 'cn' in request body"}, 400

    key = data["key"]
    cn = data["cn"]

    config = create_config(cn, key)

    return config, 200
