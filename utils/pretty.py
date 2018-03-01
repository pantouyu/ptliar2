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

__all__ = ["psize", "ptime", "KILO", "MEGA", "GIGA", "TERA", "HOUR", "MIN"]

KILO = 1024
MEGA = KILO*KILO
GIGA = MEGA*KILO
TERA = GIGA*KILO

def _pretty_size(b):
    b = float(b)
    for sz, fmt in zip([TERA, GIGA, MEGA, KILO], ["%sTB", "%sGB", "%sMB", "%sKB"]):
        if b >= sz:
            return fmt % round(b / sz, 1)
    return "%sB" % round(b, 1)

MIN  = 60
HOUR = 3600

def _pretty_time(t):
    t = int(t)
    h, t = divmod(t, HOUR)
    m, s = divmod(t, MIN)
    if h:
        return "%d:%02d:%02d" % (h, m, s)
    return "%02d:%02d" % (m, s)

psize = _pretty_size
ptime = _pretty_time

