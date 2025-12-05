from flask import Flask, request, send_file

from src.authorization import vpn
from src.certifcate import create_cert


app = Flask(__name__)


@app.route("/generate", methods=["POST"])
@vpn(roles=["admin"])
def generate_vpn_config():
    data = request.files['file']

    if data.filename == '':
        return {"error": "No selected file"}, 400

    config = create_cert(data.filename.split('.')[0], data.read().decode('utf-8'))

    return send_file(config, as_attachment=True), 200


@app.route("/connect", methods=["GET"])
@vpn
def connect():
    pass
