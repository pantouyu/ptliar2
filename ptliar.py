#!/usr/bin/python2.6
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

from __future__ import with_statement
from threading import Thread, Lock
from httplib import HTTPConnection, HTTPSConnection
from logging import getLogger, Formatter, FileHandler, StreamHandler, DEBUG, INFO
from getopt import getopt, GetoptError
from random import randint, uniform
from time import time, sleep
from sys import stdout, argv

from config import *
from clients import BT_CLIENTS, DEFAULT_CLIENT, client_list
from utils.encode import bencode, bdecode, gzip_decode, urlencode, get_infohash
from utils.pretty import ptime, psize, HOUR, MIN, MEGA, KILO
from utils.system import ptl_error, ptl_exit, interrupt_on, interrupt_off, ipv6_addr
from utils.bt import client_key, peer_id, hex_to_byte, split_url, is_scrapable
from utils.fs import move, remove, mkdir, join, size, ls_ext, read_int, write_int

__author__  = "ptliar.com"
__version__ = "v2.0.11"
__date__    = "2011/12/25"
__licence__ = "gnu general public license v2.0"
__url__     = "http://ptliar.com"
__email__   = "s@ptliar.com"
__doc__     = """\
ptliar %(version)s by %(author)s, %(date)s
url: %(url)s
email: %(email)s
quite happy with python 2.6.4
usage: ptliar [options]
options:
    -h  help, print this message
    -l  print the list of supported clients
    -m  maximum up bandwidth, in KB/s, (default: %(DEFAULT_MAX_UP_SPEED)s)
    -M  maximum down bandwidth, in KB/s, (default: %(DEFAULT_MAX_DOWN_SPEED)s)
    -s  maximum speed per torrent, in KB/s, (default: %(DEFAULT_MAX_TORRENT_SPEED)s)
    -c  client to emulate (default: %(DEFAULT_CLIENT)s)
    -t  timer, in hours (default: %(LUCKY_NUMBER)s)
    -p  fake port number (default: random)
    -e  report ipv6 address to tracker (default: disabled)
    -z  enable 'zero-rate' (default: disabled)
    -n  disable 'scrape' (default: enabled)
    -f  skip some sleep
    -v  verbose
press [Ctrl+C] for exit""" % {
    "author"    : __author__,
    "version"   : __version__,
    "date"      : __date__,
    "url"       : __url__,
    "email"     : __email__,
    "DEFAULT_MAX_UP_SPEED"      : DEFAULT_MAX_UP_SPEED,
    "DEFAULT_MAX_DOWN_SPEED"    : DEFAULT_MAX_DOWN_SPEED,
    "DEFAULT_MAX_TORRENT_SPEED" : DEFAULT_MAX_TORRENT_SPEED,
    "DEFAULT_CLIENT"            : DEFAULT_CLIENT,
    "LUCKY_NUMBER"              : LUCKY_NUMBER,
}

# Q: what the fuck is SSSS?
# A: shanghai southwest some school

# project homepage: ptliar.com
# email: s@ptliar.com

log = getLogger("ptliar")
formatter = Formatter(FMT, DATEFMT)
# delete large log file
if size(LOG_FILE) > MEGA:
    remove(LOG_FILE)
# log file handler
fh = FileHandler(LOG_FILE)
fh.setLevel(DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)

class PTLiarSettings:
    """
    global settings
    """
    def __init__(self):
        # default
        self.use_ipv6       = False             # send ipv6 addr to tracker?
        self.use_zero_rate  = False             # enable zero-rate?
        self.no_sleep       = False             # skip sleep if possible?
        self.no_scrape      = False             # disable "scrape"?
        self.client_id      = DEFAULT_CLIENT    # the client we fake
        self.timer          = LUCKY_NUMBER*HOUR # timer
        self.max_up_speed   = DEFAULT_MAX_UP_SPEED*KILO      # maximum upload bandwidth
        self.max_down_speed = DEFAULT_MAX_DOWN_SPEED*KILO    # maximum download bandwidth
        self.max_torrent_speed = DEFAULT_MAX_TORRENT_SPEED*KILO # maximum speed per torrent
        self.logging_level  = INFO              # logging level
        self.str_ipv6       = ""                # urlencoded ipv6 address
        # not set
        self.scrapable      = None              # whether "scrape" is supported
        self.client_key     = None              # our fake client-key
        self.port           = None              # our fake port number
        self.headers = {                        # the required http headers
            "Accept-Encoding" : "gzip",
            "Connection"      : "Close",
        }
        self._set_logger()

    def _set_logger(self):
        # stdout handler
        sh = StreamHandler(stdout)
        sh.setLevel(self.logging_level)
        sh.setFormatter(formatter)
        log.addHandler(sh)

    def fuck_yourself(self):
        # set ipv6 address if needed
        if self.use_ipv6:
            ipv6 = ipv6_addr()
            if not ipv6:
                ptl_error("cannot get ipv6 address")
            self.str_ipv6 = "&ipv6=%s" % urlencode(ipv6)

        # generate a port number if not given
        if not self.port:
            self.port = randint(MIN_PORT, MAX_PORT)

        # generate client key
        self.client_key = client_key()
        client_info = BT_CLIENTS[self.client_id]

        # generate peer_id : based on client chosen
        prefix = client_info["prefix"]
        pid = peer_id(prefix)
        self.quoted_peer_id = urlencode(pid)

        # generate http header[user-agent] : based on client chosen
        user_agent = client_info["user-agent"]
        self.headers.update({"User-Agent" : user_agent})

        # supports scrape?
        self.scrapable = not self.no_scrape and client_info["scrape"]

        # create directories if not exist
        for up_down in (UP, DOWN):
            mkdir(DIR[up_down])

        log.setLevel(DEBUG)
        log.debug("ptliar started, version: %s" % __version__)
        log.info("verbose            : %s"   % (self.logging_level == DEBUG))
        log.info("ipv6               : %s"   % self.use_ipv6)
        log.info("zero_rate          : %s"   % self.use_zero_rate)
        log.info("timer              : %s"   % ptime(self.timer))
        log.info("max up bandwidth   : %s/s" % psize(self.max_up_speed))
        log.info("max down bandwidth : %s/s" % psize(self.max_down_speed))
        log.info("max torrent speed  : %s/s" % psize(self.max_torrent_speed))
        log.info("fake bt client     : %s"   % self.client_id)

class TicketSeller:
    """
    ticket-based speed manager
    """
    def __init__(self):
        self._tickets_left = { UP: ALL_TICKETS, DOWN: ALL_TICKETS }
        self._locks = { UP: Lock(), DOWN: Lock() }

    def fuck_yourself(self):
        self._safe_tickets = {
            UP   : ps.max_torrent_speed * ALL_TICKETS / ps.max_up_speed,
            DOWN : ps.max_torrent_speed * ALL_TICKETS / ps.max_down_speed,
        }

    def _has_no_luck(self, got):
        """
        zero rate stuff
        """
        luck = uniform(0, 1)
        if (got > ZR_GOT_L3 and luck < ZR_LUCK_L3) or \
           (got > ZR_GOT_L2 and luck < ZR_LUCK_L2) or \
           (got > ZR_GOT_L1 and luck < ZR_LUCK_L1):
            return True
        return False

    @property
    def up_speed(self):
        used_tickets = ALL_TICKETS - self._tickets_left[UP]
        speed = ps.max_up_speed * used_tickets / ALL_TICKETS
        return speed

    @property
    def down_speed(self):
        used_tickets = ALL_TICKETS - self._tickets_left[DOWN]
        speed = ps.max_down_speed * used_tickets / ALL_TICKETS
        return speed

    def get_up_speed(self, torrent):
        return ps.max_up_speed * torrent.tickets[UP] / ALL_TICKETS

    def get_down_speed(self, torrent):
        return ps.max_down_speed * torrent.tickets[DOWN] / ALL_TICKETS

    def get_tickets(self, torrent, up_down):
        """
        get random number of tickets
        """
        with self._locks[up_down]:
            safe_tickets = self._safe_tickets[up_down]
            if up_down == UP and torrent.down_peers < 8:
                safe_tickets /= 2
            possible_tickets = min(self._tickets_left[up_down], safe_tickets)
            got = randint(0, possible_tickets)
            if ps.use_zero_rate and self._has_no_luck(got):
                got = 0
            self._tickets_left[up_down] += torrent.tickets[up_down] - got
        return got

    def return_tickets(self, torrent, up_down):
        """
        return some lottery tickets
        """
        with self._locks[up_down]:
            self._tickets_left[up_down] += torrent.tickets[up_down]
        torrent.tickets[up_down] = 0
        torrent.speed[up_down] = 0

class Torrent:
    """
    torrent module
    """
    conns = { "http": HTTPConnection, "https" : HTTPSConnection }

    def __init__(self):
        self.status = "started"     # some event or "noevent"
        self.uploaded   = 0         # bytes fake uploaded (committed)
        self.downloaded = 0         # bytes fake downloaded (comitted)
        self.up_peers   = 0         # number of complete peers
        self.down_peers = 0         # number of incomplete peers
        self.speed   = { UP : 0, DOWN : 0 }
        self.tickets = { UP : 0, DOWN : 0 }
        self.last_commit_time = 0   # the time of last commit (now/in the past)
        self.next_commit_time = 0   # the time of next commit (in the future)

    def hash(self):
        """
        uniquely identify a torrent
        """
        return (self.domain, self.infohash)

    @property
    def scrapable(self):
        return ps.scrapable and is_scrapable(self.path)

    @property
    def up(self):
        return self.up_down == UP

    @property
    def down(self):
        return self.up_down == DOWN

    def load(self, up_down, filename):
        """
        load torrent information from a file
        """
        self.filename = filename
        self.name = filename.rpartition(".")[0][:20]
        self.up_down = up_down
        full_path = join(DIR[up_down], filename)
        with open(full_path, "rb") as f:
            meta_info = bdecode(f.read())

        # generating Infohash
        info = meta_info["info"]
        infohash = get_infohash(info)

        # get url infomation
        announce = meta_info["announce"]
        self.scheme, self.domain, self.path = split_url(announce)

        # get infohash
        self.infohash = hex_to_byte(infohash)
        self.quoted_infohash = urlencode(self.infohash)

        # get torrent size
        if "files" in info:
            # a mutli-file torrent (having a sub-directory structure)
            self.size = sum(map(lambda x:x["length"], info["files"]))
        elif "length" in info:
            # The following table gives the structure of a single-file torrent
            # (does not have a sub-directory structure)
            self.size = int(info["length"])
        else:
            # weird cases
            self.size = int(info["piece length"])

        # get left
        if up_down == UP:
            self.left = 0
        elif up_down == DOWN:
            left_file = join(DIR[DOWN], "%s.left" % self.filename)
            left = read_int(left_file)
            if not left or left > self.size:
                left = self.size
            self.left = left

    @property
    def is_ready(self):
        return self.status == "stopped" or \
              (self.status != "error" and self.next_commit_time <= time())

    def _update_status(self):
        """
        update uploaded/downloaded/status etc.
        """
        # update 'uploaded'
        if self.last_commit_time:
            delta = time() - self.last_commit_time
            self.uploaded += int(ts.get_up_speed(self) * delta)

        if self.up:
            return

        # update 'downloaded' and 'left'
        delta = time() - self.last_commit_time
        down_size = int(ts.get_down_speed(self) * delta)
        down_size = min(self.left, down_size)
        self.left -= down_size
        self.downloaded += down_size

        left_file = join(DIR[DOWN], "%s.left" % self.filename)
        if self.left <= 0:
            # completed
            log.info("completed [%20s]" % self.name)
            ts.return_tickets(self, DOWN)
            self.up_down = UP

            # move torrents from down_torrents to up_torrents
            src = join(DIR[DOWN], self.filename)
            dst = join(DIR[UP],  self.filename)
            remove(left_file)
            move(src, dst)

        else:
            # not yet, record progress
            write_int(left_file, self.left)

    @property
    def _first_char(self):
        return "&" if "?" in self.path.rpartition("/")[-1] else "?"

    def _get_commit_string(self):
        """
        return the query url based on the status of the torrent
        """
        # set up inumwant
        numwant = 0 if self.status == "stopped" else NUMWANT
        req =  self.path + self._first_char
        req += "info_hash=%s" % self.quoted_infohash
        req += "&peer_id=%s" % ps.quoted_peer_id
        req += "&port=%s" % ps.port
        req += "&uploaded=%s" % self.uploaded
        req += "&downloaded=%s" % self.downloaded
        req += "&left=%s" % self.left
        req += "&corrupt=0"
        req += "&key=%s" % ps.client_key
        if self.status in ("started", "completed", "stopped"):
            req += "&event=%s" % self.status
        req += "&numwant=%s" % numwant
        req += "&compact=1&no_peer_id=1"
        if ps.use_ipv6 and self.status != "stopped":
            req += ps.str_ipv6
        log.debug("commit_string [%20s] %s" % (self.name, req))
        return req

    def _get_scrape_string(self):
        """
        return the query url for scrape
        """
        split = list(self.path.rpartition("/"))
        split[-1] = split[-1].replace("announce", "scrape", 1)
        scrape_link = "".join(split)
        req =  scrape_link + self._first_char
        req += "info_hash=%s" % self.quoted_infohash
        log.debug("scrape_string [%20s] %s" % (self.name, req))
        return req

    def _send_message(self, path, method):
        """
        send the lie to tracker
        if success: return True, response
        if failure: return False, {"err_msg" : reason}
        """
        cnt_redir = 0           # count of redirections
        scheme = self.scheme    # "http" or "https"
        domain = self.domain
        while cnt_redir < REDIRECT_RETRY:
            cnt_tried = 0           # count of retries
            while True:
                # if this is a retry, append a string in output to indicate it
                retry = " retry %s" % cnt_tried if cnt_tried else ""
                if method == "scrape":
                    log.info("%s [%20s] %s%s" % (method, self.name, scheme, retry))
                elif method == "commit":
                    log.info("%s [%20s] up:%s down:%s left:%s event:%s %s%s" % \
                                   (method, self.name,
                                    psize(self.uploaded),
                                    psize(self.downloaded),
                                    psize(self.left),
                                    self.status, scheme, retry))

                conn_class = Torrent.conns.get(scheme)
                if not conn_class:
                    raise Exception("Weird scheme: %s" % scheme)
                try:
                    conn = None
                    conn = conn_class(domain, timeout=CONNECTION_TIMEOUT)
                    conn.putrequest("GET", path, True, True)
                    conn.putheader("Host", domain)
                    conn.putheader("User-Agent",      ps.headers["User-Agent"])
                    conn.putheader("Accept-Encoding", ps.headers["Accept-Encoding"])
                    conn.putheader("Connection",      ps.headers["Connection"])
                    conn.endheaders()
                    response = conn.getresponse()
                    status  = response.status
                    headers = response.getheaders()
                    data    = response.read()
                    if status not in (500, 501, 502):
                        conn.close()
                        break
                    # retry when encounters 500, 502, count them as timeout
                    log.error("internal server error [%20s]" % self.name)
                except Exception as e:
                    log.error("%s:%s [%20s]" % (type(e).__name__, e, self.name))
                if conn:
                    conn.close()
                cnt_tried += 1
                if cnt_tried >= TIMEOUT_RETRY:
                    # seems like the tracker ignored us
                    return False, {"err_msg": "timeout several times"}
                sleep(SLEEP_TIMEOUT)
            if status in (300, 301, 302, 303, 307):
                # handling redirection
                redir_url = None
                for (k, v) in headers:
                    if k.lower() == "location":
                        redir_url = v
                        break
                if redir_url == None:
                    # caught in a bad redirection
                    return False, {"err_msg": "bad redirection"}
                # get the new url to visit
                cnt_redir += 1
                scheme, domain, path = split_url(redir_url)
                log.debug("redirect %s [%20s] url:%s" % (status, self.name, redir_url))
                continue
            elif status != 200:
                # unsupported HTTP status
                return False, {"err_msg": "not supported HTTP status: %s" % status}

            # 200, succeeded in getting response
            bencoded_info = None
            for (k, v) in headers:
                if k.lower() == "content-encoding":
                    if v.lower() == "gzip":
                        # it's gzipped
                        bencoded_info = gzip_decode(data)
                    break
            if not bencoded_info:
                bencoded_info = data

            # B decoding
            try:
                meta_info = bdecode(bencoded_info)
            except TypeError:
                return False, {"err_msg": "bad response format"}
            return True, meta_info
        return False, {"err_msg": "too many redirections"}

    def _error(self, err_msg, set_status=True):
        ts.return_tickets(self, UP)
        ts.return_tickets(self, DOWN)
        if set_status:
            # we will retry for this kind of failure
            self.status = "error"
        log.error("[%s] reason: %s" % (self.name, err_msg))

    def scrape(self):
        scrape_string = self._get_scrape_string()
        is_success, meta_info = self._send_message(scrape_string, "scrape")
        if not is_success:
            log.warning("scrape: %s" % meta_info["err_msg"])
            return
        if "files" not in meta_info or self.infohash not in meta_info["files"]:
            log.warning("scrape: bad scrape response")
            return
        meta_info = meta_info["files"][self.infohash]

        incomplete = meta_info.get("incomplete", -1)
        complete = meta_info.get("complete", -1)
        if incomplete == -1 or complete == -1:
            log.warning("scrape: bad scrape response")
            return

        self.up_peers   = int(complete)
        self.down_peers = int(incomplete)
        log.debug("scrape [%20s] incomplete %s complete %s" % \
                     (self.name, self.down_peers, self.up_peers))

    def commit(self):
        try:
            self._commit()
        except:
            log.exception("exception in commit")

    def _commit(self):
        if self.status == "started" and self.scrapable:
            self.scrape()

        self._update_status()

        req = self._get_commit_string()
        is_success, meta_info = self._send_message(req, "commit")

        if not is_success:
            self._error(meta_info["err_msg"], False)
            self.last_commit_time = time()
            self.next_commit_time = self.last_commit_time + 30*MIN
            return

        if self.status == "stopped":
            # stopped, that's it
            log.info("receive [%20s] up:%s down:%s" % \
                        (self.name, psize(self.uploaded), psize(self.downloaded)))
            return

        failure_reason = meta_info.get("failure reason", -1)
        if failure_reason != -1:
            # failure reason received
            if "failure reason" in CRITICAL_RESPONSES:
                self._error("server rejected [%s]" % failure_reason)
                return
            # not really critical, try 30 mis later
            self._error("server rejected [%s]" % failure_reason, False)
            self.last_commit_time = time()
            self.next_commit_time = self.last_commit_time + 30*MIN
            return

        interval = meta_info.get("interval", -1)
        if interval == -1:
            # weird, inteval not given
            self._error("inteval not given")
            return

        # interval received, set next_commit_time
        self.last_commit_time = time()
        self.next_commit_time = self.last_commit_time + interval

        # get 'up_peers' and 'down_peers'
        complete = meta_info.get("complete", -1)
        incomplete = meta_info.get("incomplete", -1)
        if complete != -1 and incomplete != -1:
            # got overall status from commit response
            self.up_peers   = int(complete)
            self.down_peers = int(incomplete)
        elif self.scrapable:
            if self.status != "started":
                # scrape supported and not yet scraped
                self.scrape()
        elif "peers" in meta_info:
            # just assume [active peers] = [total peers] / [a certain rate]
            len_peers = len(meta_info["peers"])
            self.up_peers   = len_peers / PEER_UPLOAD_RATE
            self.down_peers = len_peers / PEER_DOWNLOAD_RATE

        # get some uploading speed?
        if (self.up and self.down_peers) or \
               (self.down and self.tickets[DOWN] and self.down_peers > 1):
            self.tickets[UP] = ts.get_tickets(self, UP)
            self.speed[UP] = ts.get_up_speed(self)
        else:
            ts.return_tickets(self, UP)

        # get some downloading speed?
        if self.down and self.down_peers > 1 and self.up_peers > 1:
            # fake download only when
            # there is actually someone downloading and someone uploading
            self.tickets[DOWN] = ts.get_tickets(self, DOWN)
            self.speed[DOWN] = ts.get_down_speed(self)
            if self.speed[DOWN]:
                left = self.left / self.speed[DOWN]
                if left < interval:
                    self.next_commit_time = self.last_commit_time + left + 10
        else:
            ts.return_tickets(self, DOWN)

        # clear the event
        if self.status in ("started", "completed"):
            self.status = "noevent"

        log.info("receive [%20s] int:%s " \
                 "(down_peer:%s up_speed:%s/s) " \
                 "(up_peer:%s down_speed:%s/s)" % \
                     (self.name, ptime(interval),
                      self.down_peers, psize(self.speed[UP]),
                      self.up_peers, psize(self.speed[DOWN])))

class TorrentMerchant():
    """
    torrent manager
    """
    def __init__(self):
        self.torrents = {}
        self.files = set()
        self.done = False

    def _load_torrents(self):
        """
        detect folder changes
        """
        for up_down in (UP, DOWN):
            for f in ls_ext(DIR[up_down], ".torrent"):
                if f in self.files:
                    continue
                self.files |= set([f])
                try:
                    torrent = Torrent()
                    torrent.load(up_down, f)
                except TypeError:
                    log.error("bad torrent format [%s]" % f)
                    continue
                except:
                    log.exception("exception in loading torrent [%s]" % f)
                    continue
                torrent_id = torrent.hash()
                if torrent_id in self.torrents:
                    log.warning("duplicate torrent [%s]" % f)
                    continue
                self.torrents[torrent_id] = torrent
                log.info("added [%20s] size:%s left:%s for %s" % \
                             (torrent.name,
                              psize(torrent.size),
                              psize(torrent.left),
                              WORD[up_down]))

    def _fool_around(self):
        def run_threads(box):
            for th in box:
                th.start()
            for th in box:
                th.join()

        thread_box = []
        for torrent in self.torrents.values():
            if not torrent.is_ready:
                continue
            thread_box.append(Thread(target=torrent.commit))
            if len(thread_box) == CONNECTION_PER_BOX:
                run_threads(thread_box)
                thread_box = []
                if not ps.no_sleep:
                    sleep(SLEEP_THREAD)
        run_threads(thread_box)

        # calculate committed values
        all_torrents = self.torrents.values()
        uploaded = 0
        downloaded = 0
        for torrent in all_torrents:
            uploaded += torrent.uploaded
            downloaded += torrent.downloaded

        log.info("time: %s up_speed: %s/s down_speed: %s/s "\
                 "committed [up: %s down: %s]" % \
                    (ptime(time() - self.started),
                     psize(ts.up_speed),
                     psize(ts.down_speed),
                     psize(uploaded),
                     psize(downloaded)))

        if self.done:
            # say goodbye
            elapsed = time() - self.started
            log.info("time elapsed: %s" % ptime(elapsed))
            log.info("avg up speed: %s/s"   % psize(uploaded / elapsed))
            log.info("avg down speed: %s/s" % psize(downloaded / elapsed))
            log.debug("<= PTLiar ended")
            print "Bye~"
            ptl_exit(0)

        active_torrents = filter(lambda t:t.status != "error", all_torrents)
        if len(active_torrents) < 1:
            ptl_error("no torrents available")

        # calculate how long should we sleep
        next_commit = min(map(lambda t:t.next_commit_time, active_torrents))
        left = max(0, next_commit - time())

        # sleep one more second than needed
        zzz = min(SLEEP_SCAN, left + 1)
        log.info("next commit: %s from now, sleep for %s.." % \
                 (ptime(left), ptime(zzz)))
        print "press [Ctrl+C] to leave"
        try:
            interrupt_on()
            sleep(zzz)
            interrupt_off()
        except (KeyboardInterrupt, SystemExit):
            # gracefully shutdown
            interrupt_off()
            self.done = True
        if time() >= self.started + ps.timer:
            # timer
            self.done = True
        if self.done:
            log.info("stopping...")
            for torrent in active_torrents:
                torrent.status = "stopped"
            return
        # check whether we've got new torrent
        self._load_torrents()

    def fool_around(self):
        """
        fool the trackers around
        """
        try:
            self._load_torrents()
        except Exception:
            log.exception("exception in fool_around")
            ptl_exit(2)
        self.started = time()
        try:
            while True:
                self._fool_around()
        except Exception:
            log.exception("exception in fool_around")

ps = PTLiarSettings()
ts = TicketSeller()
tm = TorrentMerchant()

def _usage():
    print __doc__

def main(argv):
    interrupt_off()
    try:
        opts, args = getopt(argv, "c:DefhM:m:nlp:s:t:vz")
    except GetoptError:
        _usage()
        ptl_exit(2)

    def parse_int(i):
        if i.isdigit():
            return int(i)
        return 0

    for opt, arg in opts:
        if opt == "-h":
            _usage()
            ptl_exit(0)
        if opt == "-l":
            client_list()
            ptl_exit(0)
        if opt == "-m":
            ps.max_up_speed = parse_int(arg) * KILO
            if ps.max_up_speed <= 0:
                ptl_error("max upload bandwidth must be a positive integer, in KB/s")
        elif opt == "-M":
            ps.max_down_speed = parse_int(arg) * KILO
            if ps.max_down_speed <= 0:
                ptl_error("max download bandwidth must be a positive integer, in KB/s")
        elif opt == "-s":
            ps.max_torrent_speed = parse_int(arg) * KILO
            if ps.max_torrent_speed <= 0:
                ptl_error("max torrent speed must be a positive integer, in KB/s")
        elif opt == "-p":
            ps.port = parse_int(arg)
            if ps.port < MIN_PORT or ps.port > MAX_PORT:
                ptl_error("port number should be within (%s, %s)" % \
                              (MIN_PORT, MAX_PORT))
        elif opt == "-v":
            ps.logging_level = DEBUG
        elif opt == "-e":
            ps.use_ipv6 = True
        elif opt == "-z":
            ps.use_zero_rate = True
        elif opt == "-f":
            ps.no_sleep = True
        elif opt == "-n":
            ps.no_scrape = True
        elif opt == "-c":
            if arg not in BT_CLIENTS:
                ptl_error("client not in supported client-list, see option -l")
            ps.client_id = arg
        elif opt == "-t":
            ps.timer = parse_int(arg) * HOUR
            if ps.timer < 1:
                ptl_error("timer must be a positive integer, in hours")
    print BANNER % { "version" : __version__, "date" : __date__, "url" : __url__ }
    if not ps.no_sleep:
        sleep(SLEEP_BANNER)
    ps.fuck_yourself()
    ts.fuck_yourself()
    if not ps.no_sleep:
        sleep(SLEEP_SETTINGS)
    tm.fool_around()

if __name__ == "__main__":
    main(argv[1:])

