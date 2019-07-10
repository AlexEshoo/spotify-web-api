import base64
import json
import requests
from urllib.parse import urljoin

from spotify.auth import SpotifyClientCredentials, SpotifyOAuth


# TODO: Handle Paging Objects

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

    def _request(self, method, endpoint, query=None, payload=None, content_type="application/json"):
        url = slash_join(self.base_endpoint, endpoint)
        headers = {"Authorization": f"Bearer {self.auth.access_token}",
                   "Content-Type": content_type}
        query = query or {}

        if self.market:
            query["market"] = self.market

        response = requests.request(method, url, headers=headers, params=query, data=payload)

        # print(response.status_code, response.content, response.headers)

        if response.status_code == requests.codes.OK:
            if response.content:  # Some requests have empty bodies...
                return response.json()
            else:
                return {"result": "Success"}  # TODO: make this better.
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

    def get_recommendations(self, seed_artists=None, seed_genres=None, seed_tracks=None,
                            limit=None, market=None, **kwargs):
        """
        kwargs contains tunable Track attributes. TODO: add these explicitly?
        """
        endpoint = "recommendations"

        if not any((seed_artists, seed_genres, seed_tracks)):
            return None  # TODO: Don't fail silently? Let request fail to handle this?

        seed_artists = seed_artists or []
        seed_tracks = seed_tracks or []
        seed_genres = seed_genres or []

        query = {'seed_artists': ",".join(seed_artists),
                 'seed_genres': ",".join(seed_genres),
                 'seed_tracks': ",".join(seed_tracks),
                 'limit': limit,
                 'market': market}

        query.update(kwargs)  # Add in other parameters from API.

        return self._request("GET", endpoint, query=query)

    def get_recommendation_genres(self):
        endpoint = "recommendations/available-genre-seeds"
        return self._request("GET", endpoint)

    def get_all_new_releases(self, country=None, limit=None, offset=None):
        endpoint = "browse/new-releases"
        query = {'country': country, 'limit': limit, 'offset': offset}

        return self._request("GET", endpoint, query=query)

    def get_all_featured_playlists(self, country=None, locale=None, timestamp=None, limit=None, offset=None):
        endpoint = "browse/featured-playlists"
        query = {'country': country, 'locale': locale, 'timestamp': timestamp, 'limit': limit, 'offset': offset}

        return self._request("GET", endpoint, query=query)

    def remove_tracks_from_playlist(self, playlist_id, track_uris, snapshot_id=None):
        endpoint = slash_join("playlists", playlist_id, "tracks")
        payload = {"tracks": [{"uri": uri} for uri in track_uris]}
        if snapshot_id:
            payload["snapshot_id"] = snapshot_id

        return self._request("DELETE", endpoint, payload=json.dumps(payload))

    def add_tracks_to_playlist(self, playlist_id, track_uris, position=None):
        endpoint = slash_join("playlists", playlist_id, "tracks")
        payload = {"uris": track_uris,
                   "position": position}

        return self._request("POST", endpoint, payload=json.dumps(payload))

    def get_playlist_tracks(self, playlist_id, fields=None, limit=None, offset=None, market="from_token"):
        endpoint = slash_join("playlists", playlist_id, "tracks")
        query = {"fields": fields,
                 "limit": limit,
                 "offset": offset,
                 "market": market}

        return self._request("GET", endpoint, query=query)

    def create_playlist(self, name, user_id=None, public=None, collaborative=None, description=None):
        if user_id is None:
            user_id = self.get_current_user_profile().get("id")  # Use current user if one not explicitly provided

        endpoint = slash_join("users", user_id, "playlists")

        payload = {"name": name,
                   "public": public,
                   "collaborative": collaborative,
                   "description": description}

        return self._request("POST", endpoint, payload=json.dumps(payload))

    def upload_custom_playlist_cover_image(self, playlist_id, image_path):
        endpoint = slash_join("playlists", playlist_id, "images")
        with open(image_path, 'rb') as jpg_file:
            jpg_data = jpg_file.read()

        encoded_jpg = base64.b64encode(jpg_data).decode()
        print(encoded_jpg)

        return self._request("PUT", endpoint, content_type="image/jpg", payload=encoded_jpg)

    def get_playlist_cover_image(self, playlist_id):
        endpoint = slash_join("playlists", playlist_id, "images")

        return self._request("GET", endpoint)

    def list_user_playlists(self, user_id, limit=None, offset=None):
        endpoint = slash_join("users", user_id, "playlists")
        query = {'user_id': user_id, 'limit': limit, 'offset': offset}

        return self._request("GET", endpoint, query=query)

    def get_playlist(self, playlist_id, fields=None, market="from_token"):
        endpoint = slash_join("playlists", playlist_id)
        query = {"fields": fields,
                 "market": market}

        return self._request("GET", endpoint, query=query)

    def replace_playlist_tracks(self, playlist_id, track_uris=None):
        endpoint = slash_join("playlists", playlist_id, "tracks")
        track_uris = track_uris or []
        payload = {"uris": track_uris}

        return self._request("PUT", endpoint, payload=json.dumps(payload))

    def list_current_user_playlists(self, limit=None, offset=None):
        endpoint = "me/playlists"
        query = {"limit": limit, "offset": offset}

        return self._request("GET", endpoint, query=query)

    def change_playlist_details(self, playlist_id, name=None, public=None, collaborative=None, description=None):
        endpoint = slash_join("playlists", playlist_id)

        payload = {}
        if name is not None:
            payload["name"] = name
        if public is not None:
            payload["public"] = public
        if collaborative is not None:
            payload["collaborative"] = collaborative
        if description is not None:
            payload["description"] = description

        return self._request("PUT", endpoint, payload=json.dumps(payload))

    def reorder_track_playlists(self, playlist_id, range_start, insert_before, range_length=None, snapshot_id=None):
        endpoint = slash_join("playlists", playlist_id, "tracks")
        payload = {"range_start": range_start,
                   "insert_before": insert_before}

        if range_length:
            payload["range_length"] = range_length

        if snapshot_id:
            payload["snapshot_id"] = snapshot_id

        return self._request("PUT", endpoint, payload=json.dumps(payload))

    def search(self, q, search_tracks=False, search_artists=False, search_albums=False, search_playlists=False,
               market="from_token", limit=None, offset=None, include_external=None):
        # TODO: write code to assist query creation. Maybe different Query Object?
        endpoint = "search"

        types = {"track": search_tracks,
                 "artist": search_artists,
                 "album": search_albums,
                 "playlist": search_playlists}

        query = {"q": q,
                 "type": ",".join((k for k, b in types.items() if b)),
                 "market": market,
                 "limit": limit,
                 "offset": offset,
                 "include_external": include_external}

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

    def get_devices(self):
        endpoint = "me/player/devices"
        return self._request("GET", endpoint)

    def get_playback_state(self, market="from_token"):
        endpoint = "me/player"
        query = {"market": market}
        return self._request("GET", endpoint, query=query)

    def get_recently_played(self, limit=None, after=None, before=None):
        endpoint = "me/player/recently-played"
        query = {"limit": limit,
                 "after": after,
                 "before": before}
        return self._request("GET", endpoint, query=query)

    def get_currently_playing_track(self, market="from_token"):
        endpoint = "me/player/currently-playing"
        query = {"market": market}

        return self._request("GET", endpoint, query=query)

    def pause_playback(self, device_id=None):
        endpoint = "me/player/pause"
        query = {"device_id": device_id}

        return self._request("PUT", endpoint, query=query)

    def seek_playback(self, position_ms, device_id=None):
        endpoint = "me/player/seek"
        query = {"position_ms": position_ms,
                 "device_id": device_id}

        return self._request("PUT", endpoint, query=query)

    def set_playback_repeat_mode(self, state="off", device_id=None):
        endpoint = "me/player/repeat"
        query = {"state": state,  # Can be 'track', 'Context', or 'off'
                 "device_id": device_id}

        return self._request("PUT", endpoint, query=query)

    def set_playback_volume(self, volume_percent, device_id=None):
        endpoint = "me/player/volume"
        query = {"volume_percent": volume_percent,
                 "device_id": device_id}

        return self._request("PUT", endpoint, query=query)

    def skip_next_track(self, device_id=None):
        endpoint = "me/player/next"
        query = {"device_id": device_id}

        return self._request("POST", endpoint, query=query)

    def skip_previous_track(self, device_id=None):
        endpoint = "me/player/previous"
        query = {"device_id": device_id}

        return self._request("POST", endpoint, query=query)

    def resume_playback(self, device_id=None, context_uri=None, uris=None, offset=None, position_ms=None):
        endpoint = "me/player/play"
        query = {"device_id": device_id}

        payload = {"context_uri": context_uri,
                   "uris": uris,
                   "offset": offset,
                   "position_ms": position_ms}

        return self._request("PUT", endpoint, query=query, payload=json.dumps(payload))

    def set_playback_shuffle_state(self, state=False, device_id=None):
        endpoint = "me/player/shuffle"
        query = {"state": state,  # Can be True or False
                 "device_id": device_id}

        return self._request("PUT", endpoint, query=query)

    def transfer_playback(self, device_ids, play=True):
        endpoint = "me/player"
        payload = {"device_ids": device_ids,
                   "play": play}

        return self._request("PUT", endpoint, payload=json.dumps(payload))

    def get_artist(self, artist_id):
        endpoint = slash_join("artists", artist_id)
        return self._request("GET", endpoint)

    def get_artists(self, artist_ids):
        endpoint = "artists"
        query = {"ids": artist_ids}

        return self._request("GET", endpoint, query=query)

    def get_artist_albums(self, artist_id, include_groups=None, country=None, limit=None, offset=None):
        endpoint = slash_join("artists", artist_id, "albums")
        query = {"include_groups": include_groups,
                 "country": country,
                 "limit": limit,
                 "offset": offset}

        return self._request("GET", endpoint, query=query)

    def get_artist_top_tracks(self, artist_id, country=None):
        endpoint = slash_join("artists", artist_id, "top-tracks")
        query = {"country": country}

        return self._request("GET", endpoint, query=query)

    def get_artist_related_artists(self, artist_id):
        endpoint = slash_join("artists", artist_id, "related-artists")

        return self._request("GET", endpoint)

    def get_album(self, album_id, market="from_token"):
        endpoint = slash_join("albums", album_id)
        query = {"market": market}

        return self._request("GET", endpoint, query=query)

    def get_albums(self, album_ids, market="from_token"):
        endpoint = "albums"
        query = {"ids": album_ids,
                 "market": market}

        return self._request("GET", endpoint, query=query)

    def get_album_tracks(self, album_id, limit=None, offset=None, market="from_token"):
        endpoint = slash_join("albums", album_id, "tracks")
        query = {"limit": limit,
                 "offset": offset,
                 "market": market}

        return self._request("GET", endpoint, query=query)
