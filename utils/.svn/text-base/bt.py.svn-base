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

__all__ = ["client_key", "peer_id", "hex_to_byte", "split_url", "is_scrapable"]

from urllib import splittype, splithost
from random import choice

_HEX = list("0123456789ABCDEF")

def _nchoice(seq, n):
    for i in xrange(n):
        yield choice(seq)

def _hex_str(n):
    return "".join(_nchoice(_HEX, n))

def hex_to_byte(h):
    return "".join(map(lambda i:chr(int(h[i:i+2], 16)), range(0, len(h), 2)))

def client_key():
    return _hex_str(8)

def peer_id(prefix):
    return "%s%s" % (prefix, hex_to_byte(_hex_str(24)))

def split_url(url):
    """
    split url to tuple (scheme, domain, path)
    ex. http://ptliar.com/hi?123 => ("http", "ptliar.com", "hi?123")
    """
    scheme, rest = splittype(url)
    domain, path = splithost(rest)
    return scheme, domain, path

def is_scrapable(link):
    """
    whether the tracker supports "scrape"
    see: http://wiki.theory.org/BitTorrentSpecification#Tracker_.27scrape.27_Convention
    """
    return link.rpartition("/")[-1].startswith("announce")
