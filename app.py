from subprocess import run

from dotenv import dotenv_values
from OpenSSL import crypto
from flask import Flask, request, send_file


app = Flask(__name__)
config = dotenv_values(".env")

REMOTE_HOST = config["REMOTE_HOST"]
REMOTE_PORT = config["REMOTE_PORT"]

def crete_cert(cn: str, req: str) -> str:
    config = open("template.ovpn", "r").read()

    with open(f"/etc/openvpn/server/easy-rsa/pki/reqs/{cn}.req", "w") as f:
        f.write(req)

    run(["/etc/openvpn/server/easy-rsa/easyrsa", "--batch", "sign-req","client", cn], cwd="/etc/openvpn/server/easy-rsa")

    config = config.replace("%REMOTE_HOST%", REMOTE_HOST)
    config = config.replace("%REMOTE_PORT%", REMOTE_PORT)
    config = config.replace("%INLINE%", inline)

    inline = open(f"/etc/openvpn/server/easy-rsa/pki/inline/private/{cn}.inline", "r").read()

    path = f"./temp/{cn}.ovpn"

    with open(path, "w") as f:
        f.write(config)

    return path


def create_config(cn: str, req: str) -> str:
    path = crete_cert(cn, req)
    return send_file(path, as_attachment=True)


@app.route("/generate", methods=["POST"])
def generate_vpn_config():
    data = request.files['file']

    if data.filename == '':
        return {"error": "No selected file"}, 400

    config = create_config(data.filename.split('.')[0], data.read().decode('utf-8'))

    return config, 200
