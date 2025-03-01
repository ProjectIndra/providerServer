from flask import Flask, request, jsonify
import base64
import logging
import requests
from flask_cors import CORS, cross_origin

# environment imports
import dotenv
dotenv.load_dotenv()


# internal imports
import virt
from mngt_server_controllers import heartbeats
from virt_controllers import telemetry,vmcrud,networkcrud

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
app.add_url_rule("/vm/activatedvms","listvms",telemetry.list_running_vms,methods=['GET'])
app.add_url_rule("/vm/inactivevms","listingactivevms",telemetry.list_inactive_vms,methods=['GET'])
app.add_url_rule("/vm/getinfo/<name>","getinfo",telemetry.get_vm_info,methods=['GET'])

##crud
app.add_url_rule("/vm/create/<name>/<vcpus>/<memory>","createvm",vmcrud.create_vm,methods=['GET'])
# vm create through qcow file
app.add_url_rule("/vm/create_qvm/<name>/<vcpus>/<memory>","create_vm_qvm",vmcrud.create_vm_qvm,methods=['GET'])
app.add_url_rule("/vm/delete/<name>","deletevm",vmcrud.delete_vm,methods=['GET'])
app.add_url_rule("/vm/activate/<name>","startvm",vmcrud.start_vm,methods=['GET'])
app.add_url_rule("/vm/ipaddresses","vms-ipaddresses",vmcrud.get_vm_ips,methods=['GET'])
app.add_url_rule("/vm/ssh/<ip>", "ssh_into_vm", vmcrud.ssh_into_vm, methods=['GET'])



#network routes

##network telemetry
app.add_url_rule("/network/list","listnetworks",telemetry.list_networks,methods=['GET'])
app.add_url_rule("/network/getinfo/<name>","getnetworkinfo",telemetry.get_network_info,methods=['GET'])

##network crud
app.add_url_rule("/network/create/<name>/<bridgeName>","createnetwork",networkcrud.create_network,methods=['GET'])
app.add_url_rule("/network/activate/<name>","startnetwork",networkcrud.activate_network,methods=['GET'])
app.add_url_rule("/network/deactivate/<name>","stopnetwork",networkcrud.deactivate_network,methods=['GET'])
app.add_url_rule("/network/delete/<name>","deletenetwork",networkcrud.delete_network,methods=['GET'])



if __name__ == '__main__':

    # check connection to libvirt daemon
    virt.check_connection()

    # check connection to management server
    # if not heartbeats.check_managment_server(os.environ.get('MNGT_URL')):
    #     print("Failed to connect to the management server")
    #     exit(1)

    app.run(debug=True)