import logging
from logging.config import dictConfig
import os

from flask import Flask, request, make_response
from flask_basicauth import BasicAuth
from apscheduler.schedulers.background import BackgroundScheduler
import requests as r
import boto3


# Pull config
codeartifact_region = os.environ["CODEARTIFACT_REGION"]
codeartifact_account_id = os.environ["CODEARTIFACT_ACCOUNT_ID"]
codeartifact_domain = os.environ["CODEARTIFACT_DOMAIN"]
codeartifact_repository = os.environ["CODEARTIFACT_REPOSITORY"]
auth_incoming = os.getenv("PROXY_AUTH")

# Logging
logging.basicConfig()
logger = logging.Logger(__name__)
# For debugging - making sure logs are printed on the console for off-the-container runs
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

# Make flask
app = Flask(__name__)
if auth_incoming:
    username, password = auth_incoming.split(":")
    app.config['BASIC_AUTH_USERNAME'] = username
    app.config['BASIC_AUTH_PASSWORD'] = password
    app.config['BASIC_AUTH_FORCE'] = True
    basic_auth = BasicAuth(app)


# Token management
client = boto3.client("codeartifact", region_name=codeartifact_region)
AUTH_TOKEN: str


def update_auth_token():
    global AUTH_TOKEN
    app.logger.info("Attempting to get a new token")
    AUTH_TOKEN = client.get_authorization_token(
        domain=codeartifact_domain,
        domainOwner=codeartifact_account_id,
        durationSeconds=43200,
    )["authorizationToken"]
    app.logger.info("Got new token")


def generate_url(path: str) -> str:
    if path.startswith("/"):
        path = path[1:]
    return f"https://aws:{AUTH_TOKEN}@{codeartifact_domain}-{codeartifact_account_id}.d.codeartifact.{codeartifact_region}.amazonaws.com/pypi/{codeartifact_repository}/simple/{path}"


@app.route("/", defaults={"path": ""})

#Initial version will not account for POST requests
#@app.route("/<path:path>", methods=["GET", "POST"])

@app.route("/<path:path>", methods=["GET"])

def proxy(path):
    app.logger.info(f"{request.method} {request.path}")

    if request.method == "GET":
        try:
            api_response = client.get_package_version_asset(
                    domain=codeartifact_domain,
                    domainOwner=codeartifact_account_id,
                    repository=codeartifact_repository,
                    format='generic',
                    namespace=request.args.get('namespace'),
                    package=request.args.get('package'),
                    packageVersion=request.args.get('version'),
                    asset=request.args.get('asset')
                    )
            file_binary = api_response['asset'].read()
            response = make_response(file_binary)
            response.headers.set('Content-Type', 'application/octet-stream')
            response.headers['Content-Disposition'] = 'inline, filename='+request.args.get('asset')
            app.logger.debug(response)
            return response
        except Exception as e:
            app.logger.info('Error getting asset {} from repository {}.'.format(request.args.get('asset'), codeartifact_repository))
            #app.logger.info(e)

#Initial version will not account for POST requests
#    elif request.method == "POST":
#        response = r.post(f"{generate_url(path)}", json=request.get_json())
#        return response.content


if __name__ == "__main__":
    update_auth_token()

    scheduler = BackgroundScheduler()
    job = scheduler.add_job(update_auth_token, "interval", seconds=21600)
    scheduler.start()

    # Used for debugging
    #app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5000)
