import base64
import json
import time
import urllib.parse

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

        self.authorize()

    def authorize(self):
        basic_auth = make_basic_authorization(self.client_id, self.client_secret)

        response = requests.post(SpotifyClientCredentials.TOKEN_ENDPOINT,
                                 data={"grant_type": "client_credentials"},
                                 headers={"Authorization": basic_auth})

        if response.status_code == 200:
            self.access_token = AccessToken(**response.json())
        else:
            raise AuthorizationError(response.reason)


class SpotifyOAuth(object):
    AUTHORIZE_ENDPOINT = "https://accounts.spotify.com/authorize"
    TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"

    def __init__(self, client_id, client_secret, redirect_uri,
                 state=None, scope=None, show_dialog=False, cache_path=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state = state
        self.scope = scope
        self.show_dialog = show_dialog
        self.cache_path = cache_path
        self.access_token = None

    def get_authorize_url(self):
        # TODO: Add in state and scope parameter
        r = requests.Request(method="GET",
                             url=SpotifyOAuth.AUTHORIZE_ENDPOINT,
                             params={"client_id": self.client_id,
                                     "response_type": "code",
                                     "redirect_uri": self.redirect_uri,
                                     "show_dialog": self.show_dialog})

        return r.prepare().url

    def get_token_code(self, url, state=None):
        # TODO: Add state validation
        # TODO: Handle Errors
        parsed = urllib.parse.urlparse(url)
        query_params = dict(urllib.parse.parse_qsl(parsed.query))

        return query_params.get("code", None)

    def get_cached_token(self):
        ...

    def cache_token(self):
        if not self.cache_path:
            raise CacheError("No cache path provided.")

        with open(self.cache_path, 'w') as f:
            json.dump(self.access_token.info, f)

    def get_access_and_refresh_tokens(self, code):
        basic_auth = make_basic_authorization(self.client_id, self.client_secret)
        response = requests.post(SpotifyOAuth.TOKEN_ENDPOINT,
                                 data={"grant_type": "authorization_code",
                                       "code": code,
                                       "redirect_uri": self.redirect_uri},
                                 headers={"Authorization": basic_auth})

        if response.status_code == requests.codes.OK:
            return AccessToken(**response.json())
        else:
            raise AuthorizationError(response.reason)

    def refresh_token(self):
        basic_auth = make_basic_authorization(self.client_id, self.client_secret)
        response = requests.post(SpotifyOAuth.TOKEN_ENDPOINT,
                                 data={"grant_type": "refresh_token",
                                       "refresh_token": self.access_token.refresh_token},
                                 headers={"Authorization": basic_auth})

        if response.status_code == requests.codes.OK:
            return AccessToken(**response.json(),
                               refresh_token=self.access_token.refresh_token)
        else:
            raise AuthorizationError(response.reason)


class AccessToken(object):
    def __init__(self, **kwargs):
        self.token = kwargs.get("access_token", None)
        self.token_type = kwargs.get("token_type", None)
        self.expires_in = kwargs.get("expires_in", None)
        if self.expires_in:
            self.expires_at = time.time() + self.expires_in

        self.scope = kwargs.get("scope", None)
        if self.scope is not None:
            if isinstance(self.scope, str):
                self.scope = self.scope.split()  # make it a list

        self.refresh_token = kwargs.get("refresh_token", None)

    @property
    def expired(self):
        return time.time() > self.expires_at

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)

    @property
    def info(self):
        return self.__dict__


class AuthorizationError(Exception):
    pass

class CacheError(Exception):
    pass
