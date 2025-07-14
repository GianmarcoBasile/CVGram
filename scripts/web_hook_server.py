from flask import Flask, request
import subprocess

app = Flask(__name__)
SECRET = "7a649f84f334d19a6f9692d4c83b725958879bc03edb55f6086160ce35f04168"

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("X-Auth-Token") != SECRET:
        return "Unauthorized", 403

    data = request.get_json()
    image = data.get("image")

    if not image:
        return "Nessun'immagine specificata", 400

    try:
        subprocess.run(f"docker pull {image}", shell=True, check=True)
        subprocess.run(f"docker service update --image {image} backend", shell=True, check=True)
        return "Deploy completato", 200
    except subprocess.CalledProcessError as e:
        return f"Deploy error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
