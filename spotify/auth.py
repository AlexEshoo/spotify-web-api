import base64
import time

import requests

def make_basic_authorization(client_id, client_secret):
    encoded = base64.urlsafe_b64encode(f"{client_id}:{client_secret}".encode()).decode()
    return f"Basic {encoded}"


class SpotifyClientCredentials(object):
    TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None

    def request_authorization(self):
        basic_auth = make_basic_authorization(self.client_id, self.client_secret)

        response = requests.post(self.TOKEN_ENDPOINT,
                                 params={"grant_type": "client_credentials"},
                                 headers={"Authorization": basic_auth})

        print(response)

class AccessToken(object):
    def __init__(self, access_token=None, token_type=None, expires_in=None):
        self.token = access_token
        self.token_type = token_type
        self.expires_in = expires_in