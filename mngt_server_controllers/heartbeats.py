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
    """

    res = requests.get(server_url + '/heartbeat')

    if res.status_code == 200:

        return True

    else:
            
        return False