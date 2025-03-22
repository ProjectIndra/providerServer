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
from mngt_server_controllers import heartbeats
from virt_controllers import telemetry, vmcrud, vmssh, networkcrud

app = Flask(__name__)
CORS(app)

# home route
@app.route('/')
def home():
    return "Welcome to the server"

#heartbeat routes
app.add_url_rule('/heartbeat', 'heartbeat', heartbeats.check_provider_server, methods=['GET'])


#vm routes

##telemetry
app.add_url_rule("/vm/activevms","listvms",telemetry.list_running_vms,methods=['GET'])
app.add_url_rule("/vm/inactivevms","listingactivevms",telemetry.list_inactive_vms,methods=['GET'])
app.add_url_rule("/vm/getinfo/<name>","getinfo",telemetry.get_vm_info,methods=['GET'])

##crud
app.add_url_rule("/vm/create","createvm",vmcrud.create_vm,methods=['POST'])
# vm create through qcow file
app.add_url_rule("/vm/create_qvm","create_vm_qvm",vmcrud.create_vm_qvm,methods=['POST'])
app.add_url_rule("/vm/delete","deletevm",vmcrud.delete_vm,methods=['POST'])
app.add_url_rule("/vm/activate","startvm",vmcrud.start_vm,methods=['POST'])
app.add_url_rule("/vm/deactivate","stopvm",vmcrud.stop_vm,methods=['POST'])


# ssh routes
# app.add_url_rule("/vm/ssh/establish/<ip>", "establish_ssh_connection_to_vm", vmssh.establish_ssh, methods=['GET'])
# app.add_url_rule("/vm/ssh/close/<ip>","close_established_connection",vmssh.close_ssh,methods=['POST   '])
app.add_url_rule("/vm/ipaddresses","vms-ipaddresses",vmssh.get_vm_ips,methods=['POST'])
app.add_url_rule("/vm/ssh/setup_wireguard","execute_command_to_active_ssh_connection",vmssh.setup_wireguard,methods=['POST'])
app.add_url_rule("/vm/ssh/start_wireguard","start_wireguard",vmssh.start_wireguard,methods=['GET'])

#network routes

##network telemetry
app.add_url_rule("/network/list","listnetworks",telemetry.list_networks,methods=['GET'])
app.add_url_rule("/network/getinfo/<name>","getnetworkinfo",telemetry.get_network_info,methods=['GET'])

##network crud
app.add_url_rule("/network/create","createnetwork",networkcrud.create_network,methods=['POST'])
app.add_url_rule("/network/activate","startnetwork",networkcrud.activate_network,methods=['POST'])
app.add_url_rule("/network/deactivate","stopnetwork",networkcrud.deactivate_network,methods=['POST'])
app.add_url_rule("/network/delete","deletenetwork",networkcrud.delete_network,methods=['POST'])



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Start the server with a specified port.")
    parser.add_argument('--port', type=int, help="Port to run the server on (default: 5000)")
    args = parser.parse_args()

    print(f"arguments: {args}")

    print("Starting server")

    def send_heartbeat():
        print("Sending heartbeat to management server")
        while True:
            res=heartbeats.check_managment_server(os.environ.get('MNGMT_URL'))
            if res==0:
                print("Failed to connect to the management server")
                exit(1)
            time.sleep(5)

    # sending heartbeat to management server every 5 seconds using a thread
    heartbeat_thread = threading.Thread(target=send_heartbeat, args=())
    heartbeat_thread.start()

    # check connection to libvirt daemon
    # virt.check_connection()

    # check connection to management server
    # if not heartbeats.check_managment_server(os.environ.get('MNGT_URL')):
    #     print("Failed to connect to the management server")
    #     exit(1)

    app.run(port=args.port,host='0.0.0.0',debug=True)