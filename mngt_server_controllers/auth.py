from flask import Flask, request, jsonify, Blueprint
from dotenv import load_dotenv
import requests
import os

load_dotenv()

def get_auth_token(init_token):
    """
    This is a function to get the authentication token
    using the INIT TOKEN
    """

    if os.environ.get("MNGMT_URL"):

        url = os.environ.get("MNGMT_URL") + "/verifyTokenForCli"

        body = {
            "cli_verification_token": init_token
        }

        response = requests.post(url, json=body)

        if response.status_code == 200:
            return response.json()["token"]
        else:
            return None

    else:
        print("MNGT_SERVER not set in environment")
        return None
