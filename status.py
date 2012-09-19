from flask import Flask

from helpers import settings

app = Flask(__name__)

@app.route('/')
def status():
    with open(settings.STATUS, 'r') as status:
        return status.read()

if __name__ == '__main__':
    app.run()
