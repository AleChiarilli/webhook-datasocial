from flask import Flask
import os

HUBSPOT_API_KEY=os.environ.get('HUBSPOT_API_KEY')

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    return "<p>Hello, World!</p>"