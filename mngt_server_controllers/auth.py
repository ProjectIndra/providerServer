from flask import Flask, request, jsonify, Blueprint
from dotenv import load_dotenv
import requests
import os

from mngt_server_controllers import system_info

load_dotenv()

def get_auth_token(init_token):
    """
    This is a function to get the authentication token
    using the INIT TOKEN
    """

    try:
        if os.environ.get("MNGMT_URL"):

            url = os.environ.get("MNGMT_URL") + "/providerServer/verifyProviderToken"

            maxvms = os.environ.get("PROVIDER_SERVER_MAX_VMS", 2)
            maxnetworks = os.environ.get("PROVIDER_SERVER_MAX_NETWORKS", 2)
            maxram = os.environ.get("PROVIDER_SERVER_MAX_RAM", 2048)
            maxcpu = os.environ.get("PROVIDER_SERVER_MAX_CPU", 2)
            maxdisk = os.environ.get("PROVIDER_SERVER_MAX_DISK", 2048)

            cpu_capacity, ram_capacity, disk_capacity = system_info.get_system_info()

            body = {
                "provider_verification_token": init_token,
                "max_vms": maxvms,
                "max_networks": maxnetworks,
                "max_ram": maxram,
                "max_cpu": maxcpu,
                "max_disk": maxdisk,
                "provider_url": os.environ.get("PROVIDER_SERVER_URL", "https://pet-muskox-honestly.ngrok-free.app"),
                "cpu_capacity": cpu_capacity,
                "ram_capacity": ram_capacity,
                "disk_capacity": disk_capacity
            }

            print(f"Sending {body} to {url}")

            response = requests.post(url, json=body)

            if response.status_code == 200:
                print("Token verified")
                return response.json()["management_server_verification_token"]
            else:
                print(f"An error occurred: {response.json()}")
                return None

        else:
            print("MNGT_SERVER not set in environment")
            return None

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
