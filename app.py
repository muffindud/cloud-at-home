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
TA_PATH = config["TA_PATH"]


def crete_cert(cn: str, req: str) -> str:
    with open(f"/etc/openvpn/server/easy-rsa/pki/reqs/{cn}.req", "w") as f:
        f.write(req)

    run(["/etc/openvpn/server/easy-rsa/easyrsa", "--batch", "sign-req","client", "ccatlabuga"], cwd="/etc/openvpn/server/easy-rsa")


def create_config(cn: str, req: str) -> str:
    crete_cert(cn, req)

    template = open("template.ovpn", "r").read()

    cert = open(CERT_PATH, "r").read()
    ca = open(CA_PATH, "r").read()
    tls_crypt = open(TA_PATH, "r").read()

    # Replace placeholders in the template
    config = template.replace("%CERT%", cert)
    config = config.replace("%CA%", ca)
    config = config.replace("%TLS_CRYPT%", tls_crypt)
    config = config.replace("%REMOTE_HOST%", REMOTE_HOST)
    config = config.replace("%REMOTE_PORT%", REMOTE_PORT)

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

    return {"config": config}, 200
