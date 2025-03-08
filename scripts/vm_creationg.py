import requests

def create_vm_qvm():

    ## first check if network exists
    network_name = "default"

    networks = requests.get("http://localhost:5000/network/list").json()
    if network_name not in networks["networks"]:
        return jsonify({"error": f"Network {network_name} does not exist"}), 400

    return networks

create_vm_qvm()
    