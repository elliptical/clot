"""This module implements the class representing torrent metainfo."""


from .backbone import Backbone
from .fields import AnnounceList, Field, Integer, NodeList, String, Timestamp, Url, UrlList


class Metainfo(Backbone):
    """Torrent file contents."""

    info = Field('info', dict)
    announce = Url('announce')
    announce_list = AnnounceList('announce-list')
    creation_date = Timestamp('creation date')
    comment = String('comment')
    created_by = String('created by')
    encoding = String('encoding', encoding='ASCII')
    publisher = String('publisher')
    publisher_url = Url('publisher-url')
    nodes = NodeList('nodes')
    url_list = UrlList('url-list')
    private = Integer('private', min_value=0, max_value=1)
    codepage = Integer('codepage', min_value=1)

    def __init__(self, raw_bytes, **kwargs):
        """Initialize self."""
        super().__init__(raw_bytes, **kwargs)
