class Track(object):
    def __init__(self, response, simplified=False):
        self.is_simplified = simplified

        self.album = Album(response.get("album"), simplified=True)
        self.artists = [Artist(a, simplified=True) for a in response.get("artists")]
        self.available_markets = response.get("available_markets")
        self.disc_number = response.get("disc_number")
        self.duration_ms = response.get("duration_ms")
        self.is_explicit = response.get("explicit")
        self.external_ids = ExternalID(response.get("external_ids"))
        self.external_urls = ExternalID(response.get("external_urls"))
        self.href = response.get("href")
        self.id = response.get("id")
        self.is_playable = response.get("is_playable")
        self.linked_from = TrackLink(**response.get("linked_from") or {})
        self.restrictions = response.get("restrictions")
        self.name = response.get("name")
        self.popularity =  response.get("popularity")
        self.preview_url = response.get("preview_url")
        self.track_number = response.get("track_number")
        self.type = response.get("type")
        self.uri = response.get("uri")
        self.is_local = response.get("is_local")


class Album(object):
    def __init__(self, response, simplified=False):
        self.is_simplified = simplified

class Artist(object):
    def __init__(self, response, simplified=False):
        self.is_simplified = simplified

class ExternalID(object):
    def __init__(self, id_info):
        (self.type, self.id), = id_info.items()

class ExternalURL(object):
    def __init__(self, url_info):
        (self.type, self.url), = url_info.items()

class TrackLink(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs