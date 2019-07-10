import os
import uuid

import spotify.auth
from spotify.client import Spotify
from spotify.models import Track

from pprint import pprint

client_id = os.environ["SPOTIFY_CLIENT_ID"]
client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
redirect_uri = os.environ["SPOTIFY_REDIRECT_URI"]

my_state = str(uuid.uuid4())
scopes = ["user-read-email",
          "user-read-private",
          "user-read-birthdate",
          "playlist-modify-public",
          "playlist-modify-private",
          "ugc-image-upload",
          "user-read-playback-state",
          "user-read-recently-played",
          "user-modify-playback-state"]

auth = spotify.auth.SpotifyOAuth.authorize_local(client_id, client_secret, redirect_uri,
                                                 state=my_state, cache_path="tmp.json", scope=scopes)

client = Spotify(auth, market="US")

pprint(Track(client.get_track("7w87IxuO7BDcJ3YUqCyMTT")).name)