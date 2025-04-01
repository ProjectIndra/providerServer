from flask import Flask, request, jsonify, Blueprint
from dotenv import load_dotenv
import requests
import os

load_dotenv()

def update_config():
    """
    This is a function to get the configuration
    """

    try:
        if request:
            os.environ["PROVIDER_SERVER_MAX_VMS"] = str(request.json()["max_vms"])
            os.environ["PROVIDER_SERVER_MAX_NETWORKS"] = str(request.json()["max_networks"])
            os.environ["PROVIDER_SERVER_MAX_RAM"] = str(request.json()["max_ram"])
            os.environ["PROVIDER_SERVER_MAX_CPU"] = str(request.json()["max_cpu"])
            os.environ["PROVIDER_SERVER_MAX_DISK"] = str(request.json()["max_disk"])
            return jsonify({"message":"Configuration updated"}),200
        else:
            return jsonify({"message":"No request body"}),400
    except Exception as e:
        return jsonify({"message":"An error occurred", "error": str(e)}),500

def get_config():
    """
    This is a function to get the configuration
    """

    try:

        print(f"Getting config from using token {os.environ.get('PROVIDER_SERVER_TOKEN')}")

        response = requests.post(os.environ.get("MNGMT_URL") + "/providerServer/getConfig",json={"management_server_verification_token": os.environ.get("PROVIDER_SERVER_TOKEN")})
        if response.status_code == 200:

            os.environ["PROVIDER_SERVER_MAX_VMS"] = str(response.json()["max_vms"])
            os.environ["PROVIDER_SERVER_MAX_NETWORKS"] = str(response.json()["max_networks"])
            os.environ["PROVIDER_SERVER_MAX_RAM"] = str(response.json()["max_ram"])
            os.environ["PROVIDER_SERVER_MAX_CPU"] = str(response.json()["max_cpu"])
            os.environ["PROVIDER_SERVER_MAX_DISK"] = str(response.json()["max_disk"])
            return True
            
        else:
            print(f"An error occurred: {response.json()}")
            return False
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False