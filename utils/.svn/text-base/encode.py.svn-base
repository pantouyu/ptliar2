# -*- coding: utf-8 -*-
#
# PTLiar, a fake seeding software
# Copyright (C) 2011 PTLiar.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

__all__ = ["gzip_decode", "get_infohash", "bencode", "bdecode", "urlencode"]

from StringIO import StringIO
from hashlib import sha1
from gzip import GzipFile

from bencode import bencode, bdecode

def gzip_decode(data):
    fileobj = StringIO(data)

    f = GzipFile(fileobj=fileobj)
    decoded = f.read()
    f.close()
    return decoded

def get_infohash(info):
    data = bencode(info)
    s = sha1()
    s.update(data)

    infohash = s.hexdigest()
    return infohash

# code simplified from python 2.7 source code
# the only different thing is that we use lower case chars
# and that it does not support arbitary 'safe'
_always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                'abcdefghijklmnopqrstuvwxyz'
                '0123456789' '_.-' '/')
_safe_map = {}
for i, c in zip(xrange(256), str(bytearray(xrange(256)))):
    _safe_map[c] = c if (i < 128 and c in _always_safe) else '%{:02x}'.format(i)

def urlencode(s):
    """
    urlencode('abc def') -> 'abc%20def'
    """
    if type(s) != str:
        raise TypeError('this shit cannot be urlencoded')

    quoter = _safe_map.__getitem__

    return ''.join(map(quoter, s))

