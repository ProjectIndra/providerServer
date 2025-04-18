from flask import jsonify, request
import subprocess

# internal import
from virt import conn

def create_network():
    """
    This function will create a network
    """
    data = request.get_json()
    name = data["name"]
    bridgeName = data.get("bridgeName", "virbr1")
    forwardMode = data.get("forwardMode", "nat")
    ipAddress = data.get("ipAddress", "192.168.122.1")
    ipRangeStart = data.get("ipRangeStart", "192.168.122.100")
    ipRangeEnd = data.get("ipRangeEnd", "192.168.122.200")
    netMask = data.get("netMask", "255.255.255.0")

    # create network xml
    network_xml = f"""
    <network>
      <name>{name}</name>
      <bridge name='{bridgeName}'/>
      <forward mode='{forwardMode}'/>
      <ip address='{ipAddress}' netmask='{netMask}'>
        <dhcp>
          <range start='{ipRangeStart}' end='{ipRangeEnd}'/>
        </dhcp>
      </ip>
    </network>
    """

    # add to temporary file
    with open("/tmp/network.xml", "w") as f:
        f.write(network_xml)

    # create network
    cmd1 = [
        "virsh",
        "net-define",
        "/tmp/network.xml",
    ]
    cmd2 = [
        "virsh",
        "net-start",
        name,
    ]

    try:
        subprocess.run(cmd1, check=True)
        subprocess.run(cmd2, check=True)
        return jsonify({"message": "Network created successfully"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500

def delete_network():
    """
    This function will delete a network
    """

    data = request.get_json()
    name = data["name"]

    # delete network
    cmd1 = [
        "virsh",
        "net-destroy",
        name
    ]

    cmd2 = [
        "virsh",
        "net-undefine",
        name
    ]

    try:
        subprocess.run(cmd1, check=True)
        subprocess.run(cmd2, check=True)
        return jsonify({"message": "Network deleted successfully"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500

def activate_network():
    """
    This function will activate a network
    """

    data = request.get_json()
    name = data["name"]

    # activate network
    cmd = [
        "virsh",
        "net-start",
        name
    ]

    try:
        subprocess.run(cmd, check=True)
        return jsonify({"message": "Network activated successfully"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500

def deactivate_network():
    """
    This function will deactivate a network
    """

    data = request.get_json()
    name = data["name"]

    # deactivate network
    cmd = [
        "virsh",
        "net-destroy",
        name,
        "&&",
        "virsh",
        "net-undefine",
        name
    ]

    try:
        subprocess.run(cmd, check=True)
        return jsonify({"message": "Network deactivated successfully"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500

