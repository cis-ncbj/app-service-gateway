from flask import Flask

app = Flask(__name__)
app.debug = True
from CISAppGateway import Views, Config

Config.conf.load()

if __name__ == '__main__':
    app.run()
