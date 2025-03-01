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
    

# doing ssh into a VM

def ssh_into_vm(ip):
    """
    This function will SSH into a specified vm through it's IP address
    """

    if not ip:
        return jsonify({"error": "IP address is required"}), 400

    username = "subbu"
    password = "Ubuntu@subbu1103"  # Use SSH keys for better security

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password, timeout=5)

        stdin, stdout, stderr = client.exec_command("hostname")  # Example command
        output = stdout.read().decode().strip()
        
        client.close()
        return jsonify({"status": "success", "output": output}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
