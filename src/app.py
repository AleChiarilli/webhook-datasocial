from flask import Flask

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    return "<p>Hello, World!</p>"