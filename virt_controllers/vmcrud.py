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
        return [] #  ssh into a VM


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
            username="avinash",
            password="avinash",
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



import paramiko
import os

def execute_wireguard_setup():
    """
    Generate a WireGuard configuration file locally, then SCP it to the VM and configure WireGuard using SSH commands.
    """
    peer_public_key = "Pb1j0VNQYKd7P3W9EfUI3GrzfKDLXv27PCZox3PB5w8="
    peer_endpoint = "192.168.0.162:51820"
    client_id = "123"
    vm_ip = "192.168.122.210"
    sudo_password = "avinash"  # Replace with actual sudo password
    INTERFACE = f"wg_{client_id}"
    local_config_path = f"/tmp/{INTERFACE}.conf"
    remote_temp_path = f"/home/avinash/{INTERFACE}.conf"
    remote_config_path = f"/etc/wireguard/{INTERFACE}.conf"

    if not vm_ip or not peer_public_key or not peer_endpoint:
        return {"error": "Missing required parameters"}, 400

    if vm_ip not in ssh_sessions:
        return {"error": "No active SSH connection for this IP"}, 400

    ssh_client = ssh_sessions[vm_ip]

    # Generate WireGuard keys locally
    private_key = os.popen("wg genkey").read().strip()
    if not private_key:
        return {"error": "Failed to generate WireGuard private key"}, 500

    public_key = os.popen(f"echo {private_key} | wg pubkey").read().strip()

    print(f"Private key: {private_key}")
    print(f"Public key: {public_key}")

    # Write the WireGuard configuration locally
    try:
        with open(local_config_path, "w") as f:
            f.write(f"""[Interface]
Address = 10.0.0.2/24
PrivateKey = {private_key}
ListenPort = 51820

[Peer]
PublicKey = {peer_public_key}
Endpoint = {peer_endpoint}
AllowedIPs = 10.0.0.0/32
PersistentKeepalive = 25
""")
    except Exception as e:
        return {"error": f"Failed to write config file: {str(e)}"}, 500

    # Ensure file exists
    if not os.path.exists(local_config_path):
        return {"error": "WireGuard config file was not created"}, 500

    # SCP the file to the VM
    try:
        scp_client = ssh_client.open_sftp()
        scp_client.put(local_config_path, remote_temp_path)
        scp_client.close()
    except Exception as e:
        return {"error": f"File transfer failed: {str(e)}"}, 500

    # Execute setup commands via SSH
    try:
        commands = [
            "set -e",  # Stop on error
            f"echo '{sudo_password}' | sudo -S apt update && sudo apt install -y wireguard",  # Install WireGuard
            f"echo '{sudo_password}' | sudo -S mv {remote_temp_path} {remote_config_path}",  # Move config
            f"""echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf""",  # Enable IP forwarding
            f"echo '{sudo_password}' | sudo -S chmod 600 {remote_config_path}",  # Set permissions
            f"echo '{sudo_password}' | sudo -S wg-quick up {INTERFACE}",  # Start WireGuard
        ]

        for cmd in commands:
            stdin, stdout, stderr = ssh_client.exec_command(cmd, get_pty=True)
            stdin.write(sudo_password + "\n")
            stdin.flush()
            error = stderr.read().decode().strip()
            if error:
                return {"error": error}, 500

        return {"status": "success", "message": "WireGuard configured successfully","public_key":public_key}, 200

    except Exception as e:
        return {"error": f"SSH command execution failed: {str(e)}"}, 500

    finally:
        os.remove(local_config_path)  # Cleanup local config file



# closing the ssh connection of the VM
def close_ssh(ip):
    """Close the SSH connection."""
    global ssh_sessions

    if ip in ssh_sessions:
        ssh_sessions[ip].close()
        del ssh_sessions[ip]
        return jsonify({"message": f"SSH connection closed for {ip}"}), 200

    return jsonify({"error": f"No active SSH connection for {ip}"}), 400


