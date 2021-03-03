"""This module implements the class representing torrent metainfo."""


from .backbone import Backbone
from .fields import Field, String, Timestamp, Url


class Metainfo(Backbone):
    """Torrent file contents."""

    info = Field('info', dict)
    announce = Url('announce')
    announce_list = Field('announce-list', list)
    creation_date = Timestamp('creation date')
    comment = String('comment')
    created_by = String('created by')
    encoding = String('encoding')
