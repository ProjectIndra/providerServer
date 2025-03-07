import requests

def check_provider_server():
    """
    This is a function to check the connection to the provider server
    from another server (management server)
    """

    return 'do some magic!',200

def check_managment_server(server_url):
    """
    This is a function to check the connection to the management server
    from another server (provider server)
    
    In this function we are sending a request to the management server
    with username and token to authenticate the provider server
    """

    url = server_url+"/heartbeat"
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "username": "admin",
        "provider_id": "provider1",
        "link":"https://pet-muskox-honestly.ngrok-free.app",
        "token": "1234"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        print(response)
        if response.status_code == 200:
            print("Connected to the management server")
            return 1
        elif response.status_code == 401:
            print("Unauthorized")
            print(f"server:{response.text}")
            return 0
        else:
            print("Failed to connect to the management server")
            return 0
    except:
        print("Failed to connect to the management server")
        return 0