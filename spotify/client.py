import requests
from urllib.parse import urljoin

from spotify.auth import SpotifyClientCredentials, SpotifyOAuth


class ClientError(Exception):
    pass


class SpotifyError(Exception):
    pass


def slash_join(*args):
    return "/".join(arg.strip("/") for arg in args)


class Spotify(object):
    def __init__(self, auth: SpotifyOAuth = None, client_id=None, client_secret=None, market=None):
        if auth:
            self.auth = auth
        elif client_id and client_secret:
            self.auth = SpotifyClientCredentials(client_id, client_secret)
        else:
            raise ClientError("No authentication provided")

        self.base_endpoint = "https://api.spotify.com/v1"
        self.market = market

    def _request(self, method, endpoint, query=None, payload=None):
        url = slash_join(self.base_endpoint, endpoint)
        headers = {"Authorization": f"Bearer {self.auth.access_token}",
                   "Content-Type": "application/json"}
        query = query or {}

        if self.market:
            query["market"] = self.market

        response = requests.request(method, url, headers=headers, params=query, data=payload)

        if response.status_code == requests.codes.OK:
            return response.json()
        else:
            print(response.reason)
            return None  # TODO: handler errors better and other responses

    def get_current_user_profile(self):
        endpoint = "me"
        return self._request("GET", endpoint)

    def get_user_profile(self, user_id):
        endpoint = slash_join("users", user_id)
        return self._request("GET", endpoint)

    def get_all_categories(self, country=None, locale=None, limit=None, offset=None):
        endpoint = "browse/categories"
        query = {"country": country,
                 "locale": locale,
                 "limit": limit,
                 "offset": offset}

        return self._request("GET", endpoint, query=query)

    def get_category(self, category_id, country=None, locale=None):
        endpoint = slash_join("browse/categories", category_id)
        query = {"country": country,
                 "locale": locale}

        return self._request("GET", endpoint, query=query)

    def get_category_playlists(self, category_id, country=None, limit=None, offset=None):
        endpoint = slash_join("browse/categories", category_id, "playlists")
        query = {"country": country,
                 "limit": limit,
                 "offset": offset}

        return self._request("GET", endpoint, query=query)

    def get_track(self, track_id):
        endpoint = slash_join("tracks", track_id)
        return self._request("GET", endpoint)

    def get_tracks(self, track_ids):
        endpoint = "tracks"
        query = {"ids": ",".join(track_ids)}
        return self._request("GET", endpoint, query=query)

    def get_audio_features(self, track_ids):
        if isinstance(track_ids, list):
            endpoint = "audio-features"
            query = {"ids": ",".join(track_ids)}
        else:
            endpoint = slash_join("audio-features", track_ids)
            query = None

        return self._request("GET", endpoint, query=query)

    def get_audio_analysis(self, track_id):
        endpoint = slash_join("audio-analysis", track_id)
        return self._request("GET", endpoint)
