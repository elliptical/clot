"""This module implements the class representing torrent metainfo."""


from .backbone import Backbone
from .fields import Field, Integer, String, Timestamp, Url


class Metainfo(Backbone):
    """Torrent file contents."""

    info = Field('info', dict)
    announce = Url('announce')
    announce_list = Field('announce-list', list)
    creation_date = Timestamp('creation date')
    comment = String('comment')
    created_by = String('created by')
    encoding = String('encoding', encoding='ASCII')
    publisher = String('publisher')
    publisher_url = Url('publisher-url')
    nodes = Field('nodes', list)
    url_list = Field('url-list', list)
    private = Integer('private', min_value=0, max_value=1)
    codepage = Integer('codepage', min_value=1)
