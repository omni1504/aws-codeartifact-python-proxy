import logging
import os

from flask import Flask, request
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
    AUTH_TOKEN = client.get_authorization_token(
        domain=codeartifact_domain,
        domainOwner=codeartifact_account_id,
        durationSeconds=43200,
    )["authorizationToken"]
    logger.info("Got new token")
    logger.debug("New token: " + AUTH_TOKEN)


def generate_url(path: str) -> str:
    if path.startswith("/"):
        path = path[1:]
    return f"https://aws:{AUTH_TOKEN}@{codeartifact_domain}-{codeartifact_account_id}.d.codeartifact.{codeartifact_region}.amazonaws.com/pypi/{codeartifact_repository}/simple/{path}"


@app.route("/", defaults={"path": ""})

#Initial version will not account for POST requests
#@app.route("/<path:path>", methods=["GET", "POST"])

@app.route("/<path:path>", methods=["GET"])

def proxy(path):
    logger.info(f"{request.method} {request.path}")

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
            response.headers.set('Content-Disposition': 'inline; filename='+request.args.get('asset'))
            return response
        except Exception as e:
            logger.info('Error getting asset {} from repository {}.'.format(request.args.get('asset'), codeartifact_repository))

#Initial version will not account for POST requests
#    elif request.method == "POST":
#        response = r.post(f"{generate_url(path)}", json=request.get_json())
#        return response.content


if __name__ == "__main__":
    update_auth_token()

    scheduler = BackgroundScheduler()
    job = scheduler.add_job(update_auth_token, "interval", seconds=21600)
    scheduler.start()

    app.run(host='0.0.0.0', port=5000)
