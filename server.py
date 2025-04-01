from flask import Flask, request, jsonify
import base64
import logging
import requests
from flask_cors import CORS, cross_origin
import threading
import os
import time
import argparse

# environment imports
import dotenv
dotenv.load_dotenv()


# internal imports
import virt
from mngt_server_controllers import heartbeats, auth, env, conf
from virt_controllers import telemetry, vmcrud, vmssh, networkcrud
from prometheus import metrics

app = Flask(__name__)
CORS(app)

app.register_blueprint(metrics.metrics_bp)

def authentication_required(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get("authorization")
        if token is None:
            return jsonify({"message":"No token provided"}),401

        if token != os.environ.get("PROVIDER_SERVER_TOKEN"):
            return jsonify({"message":"Invalid token"}),401

        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# home route
@app.route('/')
def home():
    return "Welcome to the server"

# heartbeat routes
app.add_url_rule('/heartbeat', 'heartbeat', authentication_required(heartbeats.check_provider_server), methods=['GET'])

# vm routes

## telemetry
app.add_url_rule("/vm/activevms", "listvms", authentication_required(telemetry.list_running_vms), methods=['GET'])
app.add_url_rule("/vm/inactivevms", "listingactivevms", authentication_required(telemetry.list_inactive_vms), methods=['GET'])
app.add_url_rule("/vm/getinfo/<name>", "getinfo", authentication_required(telemetry.get_vm_info), methods=['GET'])

## crud
app.add_url_rule("/vm/create", "createvm", authentication_required(vmcrud.create_vm), methods=['POST'])
# vm create through qcow file
app.add_url_rule("/vm/create_qvm", "create_vm_qvm", authentication_required(vmcrud.create_vm_qvm), methods=['POST'])
app.add_url_rule("/vm/delete", "deletevm", authentication_required(vmcrud.delete_vm), methods=['POST'])
app.add_url_rule("/vm/activate", "startvm", authentication_required(vmcrud.start_vm), methods=['POST'])
app.add_url_rule("/vm/deactivate", "stopvm", authentication_required(vmcrud.stop_vm), methods=['POST'])
app.add_url_rule("/vm/queryvm", "queryvm", authentication_required(vmcrud.query_vm), methods=['POST'])

# ssh routes
# app.add_url_rule("/vm/ssh/establish/<ip>", "establish_ssh_connection_to_vm", authentication_required(vmssh.establish_ssh), methods=['GET'])
# app.add_url_rule("/vm/ssh/close/<ip>", "close_established_connection", authentication_required(vmssh.close_ssh), methods=['POST'])
app.add_url_rule("/vm/ipaddresses", "vms-ipaddresses", authentication_required(vmssh.get_vm_ips), methods=['POST'])
app.add_url_rule("/vm/ssh/setup_wireguard", "execute_command_to_active_ssh_connection", authentication_required(vmssh.setup_wireguard), methods=['POST'])
app.add_url_rule("/vm/ssh/start_wireguard", "start_wireguard", authentication_required(vmssh.start_wireguard), methods=['GET'])

# network routes

## network telemetry
app.add_url_rule("/network/list", "listnetworks", authentication_required(telemetry.list_networks), methods=['GET'])
app.add_url_rule("/network/getinfo/<name>", "getnetworkinfo", authentication_required(telemetry.get_network_info), methods=['GET'])

## network crud
app.add_url_rule("/network/create", "createnetwork", authentication_required(networkcrud.create_network), methods=['POST'])
app.add_url_rule("/network/activate", "startnetwork", authentication_required(networkcrud.activate_network), methods=['POST'])
app.add_url_rule("/network/deactivate", "stopnetwork", authentication_required(networkcrud.deactivate_network), methods=['POST'])
app.add_url_rule("/network/delete", "deletenetwork", authentication_required(networkcrud.delete_network), methods=['POST'])

## conf update route
app.add_url_rule("/config/update", "updateconfig", authentication_required(conf.update_config), methods=['POST'])


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Start the server with a specified port.")
    parser.add_argument('--port', type=int, help="Port to run the server on (default: 5000)")
    args = parser.parse_args()

    # #check connection to libvirt daemon
    # virt.check_connection()

    if os.environ.get("PROVIDER_SERVER_TOKEN") is None or os.environ.get("PROVIDER_SERVER_TOKEN") == "":
        if os.environ.get("PROVIDER_SERVER_TOKEN_INIT") is None:
            print("No INIT token or Normal token found in environment")
            exit(1)
        else:
            print("INIT Token found in environment")
            print("Requesting token from management server")

            token = auth.get_auth_token(os.environ.get("PROVIDER_SERVER_TOKEN_INIT"))

            if token is None:
                print("Failed to get token from management server")
                exit(1)
            else:
                print("Token received from management server")
                env.set_persistent_env_var("PROVIDER_SERVER_TOKEN", token)
                print("Token saved in environment")

    if os.environ.get("PROVIDER_SERVER_MAX_VMS") is None:
        print("Requesting configuration from management server")
        if not conf.get_config():
            print("Failed to get configuration from management server")
            exit(1)
        else:
            print("Configuration received from management server")
            print("Configuration saved in environment")

    app.run(port=args.port,host='0.0.0.0',debug=True)