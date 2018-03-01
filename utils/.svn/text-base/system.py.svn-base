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

__all__ = ["ptl_exit", "ptl_error", "interrupt_on", "interrupt_off", "ipv6_addr"]

from signal import signal, SIGINT, SIG_IGN, default_int_handler
import platform, os

def ptl_exit(code):
    if platform.system() == "Windows":
        os.system("PAUSE")
    exit(code)

def ptl_error(msg):
    from logging import getLogger
    log = getLogger("ptliar")
    log.critical(msg)
    ptl_exit(2)

def interrupt_off():
    """
    disable keyboard interruption
    """
    signal(SIGINT, SIG_IGN)

def interrupt_on():
    """
    enable keyboard interruption
    """
    signal(SIGINT, default_int_handler)

def ipv6_addr():
    from socket import socket, AF_INET6, SOCK_DGRAM, gaierror
    SOME_IPV6_SITE = "ipv6.google.com"
    if socket.has_ipv6:
        try:
            s = socket(AF_INET6, SOCK_DGRAM)
            s.connect((SOME_IPV6_SITE, 0))
            return s.getsockname()[0]
        except gaierror:
            return None
    return None

