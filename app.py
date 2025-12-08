from os import path

from flask import Flask, request, send_file

from src.authorization import vpn, iam
from src.certifcate import create_cert
from src.config import EASY_RSA_PATH
from src.container import create_container, delete_container, get_container_info, update_container


app = Flask(__name__)


@app.route("/generate", methods=["POST"])
@vpn(roles=["admin"])
def generate_vpn_config():
    data = request.files['file']

    if data.filename == '':
        return {"error": "No selected file"}, 400

    if path.exists(f"{EASY_RSA_PATH}/pki/reqs/{data.filename.split('.')[0]}.req"):
        return {"error": "Request already exists"}, 400

    config = create_cert(data.filename.split('.')[0], data.read().decode('utf-8'))

    return send_file(config, as_attachment=True), 200


@app.route("/set-role", methods=["POST"])
@vpn(roles=["admin"])
def set_role():
    pass


@app.route("/connect", methods=["GET"])
def connect():
    pass


@app.route("/container", methods=["POST", "DELETE", "GET", "PUT"])
@iam
def container():
    if request.method == "POST":
        response = create_container()
        return response.content, response.status_code, response.headers.items()

    elif request.method == "DELETE":
        uuid = request.args.get("uuid")
        response = delete_container(uuid)
        return response.content, response.status_code, response.headers.items()

    elif request.method == "GET":
        uuid = request.args.get("uuid")
        response = get_container_info(uuid)
        return response.content, response.status_code, response.headers.items()

    elif request.method == "PUT":
        uuid = request.args.get("uuid")
        response = update_container(uuid)
        return response.content, response.status_code, response.headers.items()


if __name__ == "__main__":
    app.run()
