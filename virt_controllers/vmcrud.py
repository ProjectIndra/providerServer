from flask import jsonify,request

#internal import
from virt import conn

import subprocess

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

def delete_vm(name):
    """Deletes a VM. also undefines it with removing storage."""
    
    try:
        domain = conn.lookupByName(name)
        domain.destroy()
        domain.undefine().remove()
        return jsonify({"message": "VM deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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


    
