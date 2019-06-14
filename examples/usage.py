import os
import uuid

import spotify.auth
from spotify.client import Spotify

from pprint import pprint

client_id = os.environ["SPOTIFY_CLIENT_ID"]
client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
redirect_uri = os.environ["SPOTIFY_REDIRECT_URI"]

my_state = str(uuid.uuid4())

auth = spotify.auth.SpotifyOAuth.authorize_local(client_id, client_secret, redirect_uri,
                                                 state=my_state, cache_path="tmp.json")

client = Spotify(auth, market="US")

track = client.get_audio_features("1Z50OHs5UJCybYStfwIcot")

pprint(track)
