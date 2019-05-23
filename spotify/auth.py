import base64
import json
import time
import urllib.parse
import webbrowser

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
        self.scope = scope or []
        self.show_dialog = show_dialog
        self.cache_path = cache_path

        self.access_token = self.get_cached_token()

    def get_authorize_url(self):
        query_params = {"client_id": self.client_id,
                        "response_type": "code",
                        "redirect_uri": self.redirect_uri,
                        "show_dialog": self.show_dialog,
                        "state": self.state}

        if self.scope:
            query_params["scope"] = " ".join(self.scope)

        r = requests.Request(method="GET",
                             url=SpotifyOAuth.AUTHORIZE_ENDPOINT,
                             params=query_params)

        return r.prepare().url

    def get_token_code(self, url, state=None):
        # TODO: Handle Errors
        parsed = urllib.parse.urlparse(url)
        query_params = dict(urllib.parse.parse_qsl(parsed.query))

        recv_state = query_params.get("state", None)
        if state != recv_state:
            raise AuthorizationError(f"Mismatching `state` parameter in authorization url. "
                                     f"Expected: {state}, but received: {recv_state}")

        return query_params.get("code", None)

    def get_cached_token(self):
        if not self.cache_path:
            return None

        try:
            with open(self.cache_path, 'r') as f:
                token = AccessToken(**json.load(f))

        except FileNotFoundError:
            return None

        if not set(self.scope).issubset(set(token.scope)):
            # TODO Should this be a warning instead?
            return None  # Scope Changed.

        if token.expired:
            token = self.refresh_token(token.refresh_token)

        return token

    def cache_token(self, token):
        if not self.cache_path:
            return

        with open(self.cache_path, 'w') as f:
            json.dump(token.info, f)

    def get_access_and_refresh_tokens(self, code):
        basic_auth = make_basic_authorization(self.client_id, self.client_secret)
        response = requests.post(SpotifyOAuth.TOKEN_ENDPOINT,
                                 data={"grant_type": "authorization_code",
                                       "code": code,
                                       "redirect_uri": self.redirect_uri},
                                 headers={"Authorization": basic_auth})

        if response.status_code == requests.codes.OK:
            token = AccessToken(**response.json())
            self.cache_token(token)
            return token

        else:
            raise AuthorizationError(response.reason)

    def refresh_token(self, refresh_token):
        basic_auth = make_basic_authorization(self.client_id, self.client_secret)
        response = requests.post(SpotifyOAuth.TOKEN_ENDPOINT,
                                 data={"grant_type": "refresh_token",
                                       "refresh_token": refresh_token},
                                 headers={"Authorization": basic_auth})

        if response.status_code == requests.codes.OK:
            token = AccessToken(**response.json(),
                                refresh_token=refresh_token)
            self.cache_token(token)
            return token

        else:
            raise AuthorizationError(response.reason)

    @staticmethod
    def authorize_local(client_id, client_secret, redirect_uri,
                        state=None, scope=None, show_dialog=False, cache_path=None):
        """
        Convenience Constructor to create an OAuth object by verifying from a locally
        running script interactively.
        """

        auth = SpotifyOAuth(client_id, client_secret, redirect_uri,
                            state=state, scope=scope, show_dialog=show_dialog, cache_path=cache_path)

        if auth.access_token:
            try:
                auth.refresh_token(auth.access_token.refresh_token)
                print("Access Token retrieved from cache!")
                return auth  # token retrieved from cache

            except AuthorizationError:
                print("Re-Authentication Required")

        print("Open the URL shown below in a web browser and follow the on screen steps to authorize the App.")

        authorize_url = auth.get_authorize_url()
        print(authorize_url)
        webbrowser.open_new_tab(authorize_url)

        redirected = input("Enter URL Redirected to: ").strip()

        code = auth.get_token_code(redirected, state=auth.state)

        auth.access_token = auth.get_access_and_refresh_tokens(code)

        return auth


class AccessToken(object):
    def __init__(self, **kwargs):
        self.token = kwargs.get("access_token", None)
        self.token_type = kwargs.get("token_type", None)
        self.expires_in = kwargs.get("expires_in", None)
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
