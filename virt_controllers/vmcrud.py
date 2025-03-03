from flask import jsonify,request

import subprocess
import re
import paramiko

import os
import libvirt


#internal import
from virt import conn


def create_vm(name, vcpus, memory, iso_path="/var/lib/libvirt/images/ubuntu-server.iso"):
    """Creates a VM using virt-install, booting from an ISO (no disk)."""
    
    cmd = [
        "virt-install",
        "--name", name,
        "--ram", str(memory),
        "--vcpus", str(vcpus),
        "--cdrom", iso_path,  # Boot directly from ISO
        "--os-type", "linux",
        "--os-variant", "ubuntu22.04",
        "--network", "network=default",
        "--graphics", "vnc",
        "--noautoconsole"
    ]

    try:
        subprocess.run(cmd, check=True)
        
        return jsonify({"message": "VM created successfully"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500

# Create VM from existing qcow file


def create_vm_qvm(name, vcpus, memory, qvm_path="/var/lib/libvirt/images/ubuntu-vm.qcow2"):
    """Creates a VM using an existing QCOW2 disk."""
    
    cmd = [
        "virt-install",
        "--name", name,
        "--ram", str(memory),
        "--vcpus", str(vcpus),
        f"--disk={qvm_path},format=qcow2",
        "--import",
        "--os-type", "linux",
        "--os-variant", "ubuntu22.04",
        "--network", "network=default",
        "--graphics", "vnc",
        "--noautoconsole"
    ]

    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return jsonify({"message": "VM (through existing qvm) created successfully"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500  # Now returns the actual error message


def delete_vm(name):
    """Deletes a VM and removes its storage."""
    try:
        conn = libvirt.open(os.environ.get('PRV_VIRT_SYSTEM'))
        if conn is None:
            return jsonify({"error": "Failed to connect to libvirt"}), 500

        try:
            domain = conn.lookupByName(name)
        except libvirt.libvirtError:
            return jsonify({"error": f"VM '{name}' not found"}), 404

        # Get the storage path before undefining
        xml_desc = domain.XMLDesc(0)
        disk_path = extract_disk_path(xml_desc)

        # Destroy the VM if running
        if domain.isActive():
            domain.destroy()

        # Undefine the VM
        domain.undefine()

        # Remove the disk file if it exists
        if disk_path and os.path.exists(disk_path):
            os.remove(disk_path)

        return jsonify({"message": f"VM '{name}' deleted successfully"}), 200

    except libvirt.libvirtError as e:
        return jsonify({"error": str(e)}), 500

def extract_disk_path(xml_desc):
    """Extracts the disk path from VM XML description."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_desc)
    disk = root.find(".//disk[@device='disk']/source")
    return disk.get("file") if disk is not None else None


def start_vm(name):
    """
    This function will start any inactive VM
    """

    try:
        domain = conn.lookupByName(name)
        domain.create()
        return jsonify({"message": "VM started successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# getting the ip address of the vms

def get_vm_ips():
    """
    This function will get the ip addresses of all the VMs of the Host
    """

    try:
        result = subprocess.run(["virsh", "net-dhcp-leases", "default"], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        
        ip_addresses = []
        for line in lines:
            match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', line)
            if match:
                ip_addresses.append(match.group())

        return ip_addresses
    except subprocess.CalledProcessError as e:
        print("getting some error:",e)
        return []
    

                                                    #  ssh into a VM


# Dictionary to store active SSH connections
ssh_sessions = {}

# establishing ssh connection through the IP address
def establish_ssh(ip):
    """Establish an SSH connection to the VM."""
    global ssh_sessions

    if ip in ssh_sessions:
        return jsonify({"message": f"SSH connection already exists for {ip}"}), 200

    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            hostname=ip,
            username="subbu",
            password="Ubuntu@subbu1103",
            timeout=10
        )
        ssh_sessions[ip] = ssh_client
        return jsonify({"message": f"SSH connection established for {ip}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# checking the active ssh connections

# def check_ssh_status(ip):
#     """Check if SSH connection exists for a given IP."""
#     if ip in ssh_sessions:
#         return jsonify({"status": "connected", "message": f"SSH connection is active for {ip}"}), 200
#     else:
#         return jsonify({"status": "disconnected", "message": f"No active SSH connection for {ip}"}), 400



# executing the command on the vm through the ssh connection

ssh_sessions = {}



def execute_wireguard_setup():
    """
    Execute a command on the VM via an existing SSH connection.
    """

    peer_public_key = "LCpoU/slQ57/A5Fi585TxpTIII00rdAqFHUAraK67Hk="
    peer_endpoint = "192.168.1.41:5182"
    client_id = "123"
    ip = "192.168.122.172"

    if not ip or not peer_public_key or not peer_endpoint:
        return jsonify({"error": "Missing required parameters"}), 400

    if ip not in ssh_sessions:
        return jsonify({"error": "No active SSH connection for this IP"}), 400

    ssh_client = ssh_sessions[ip]

    script = f"""
    sudo DEBIAN_FRONTEND=noninteractive apt install -y wireguard -o DPkg::Lock::Timeout=30 >/dev/null 2>&1

    PRIVATE_KEY=$(wg genkey)
    PUBLIC_KEY=$(echo "$PRIVATE_KEY" | wg pubkey)

    WG_CONF="/etc/wireguard/wg_{client_id}.conf"
    INTERFACE="wg_{client_id}"
    PRIVATE_IP="10.0.0.2/24"
    PEER_IP="10.0.0.1"

    sudo tee $WG_CONF > /dev/null << EOL
[Interface]
PrivateKey = $PRIVATE_KEY
Address = $PRIVATE_IP
ListenPort = 51820

[Peer]
PublicKey = {peer_public_key}
Endpoint = {peer_endpoint}
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
EOL

    sudo systemctl enable --now wg-quick@wg_{client_id}
    sudo systemctl start wg-quick@wg_{client_id}
    """

    try:
        stdin, stdout, stderr = ssh_client.exec_command(script)
        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            return jsonify({"status": "error", "message": error}), 500
        return jsonify({"status": "success", "output": output}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# closing the ssh connection of the VM
def close_ssh(ip):
    """Close the SSH connection."""
    global ssh_sessions

    if ip in ssh_sessions:
        ssh_sessions[ip].close()
        del ssh_sessions[ip]
        return jsonify({"message": f"SSH connection closed for {ip}"}), 200

    return jsonify({"error": f"No active SSH connection for {ip}"}), 400


