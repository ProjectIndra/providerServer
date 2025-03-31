from flask import Flask, request, jsonify, Blueprint
from dotenv import load_dotenv
import requests

load_dotenv()

def get_config():
    """
    This is a function to get the configuration
    """
    if os.environ.get("MNGMT_URL"):

        url = os.environ.get("MNGMT_URL") + "/getConfig"

        response = requests.get(url)

        if response.status_code == 200:
            os.environ["PROVIDER_SERVER_MAX_VMS"] = str(response.json()["max_vms"])
            os.environ["PROVIDER_SERVER_MAX_NETWORKS"] = str(response.json()["max_networks"])
            os.environ["PROVIDER_SERVER_MAX_RAM"] = str(response.json()["max_ram"])
            os.environ["PROVIDER_SERVER_MAX_CPU"] = str(response.json()["max_cpu"])
            os.environ["PROVIDER_SERVER_MAX_DISK"] = str(response.json()["max_disk"])
            return response.json()
        else:
            return None

    else:
        print("MNGT_SERVER not set in environment")
        return None