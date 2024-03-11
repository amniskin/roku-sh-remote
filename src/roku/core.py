import curses
import logging
import socket
import string
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

import requests

logger = logging.getLogger(__name__)

class Mode(Enum):
    NORMAL = 'normal'
    INSERT = 'insert'
    EXIT = 'exit'

ORD2CHAR = {
    ord(x): x for x in string.ascii_lowercase + string.ascii_uppercase + string.digits
}
ORD2CHAR.update({
    # 9: 'back',  # tab
    # 27: 'back',  # esc key
    10: 'select',
    32: '%20',
    96: 'home',
    126: 'home',
    262: 'home',  # home key
    curses.KEY_DOWN: 'down',
    curses.KEY_UP: 'up',
    curses.KEY_LEFT: 'left',
    curses.KEY_RIGHT: 'right',
    263: 'backspace',
    265: 'volumemute',
    266: 'volumedown',
    267: 'volumeup',
})
KEYPRESS_MAP = {
    Mode.NORMAL: {
        **ORD2CHAR,
        27: 'back',
        10: 'select',
        32: 'select',
        ord('n'): 'volumedown',
        ord('m'): 'volumeup',
        ord('J'): 'volumedown',
        ord('K'): 'volumeup',
        ord('h'): 'left',
        ord('j'): 'down',
        ord('k'): 'up',
        ord('l'): 'right',
        ord('i'): Mode.INSERT,
        ord('q'): Mode.EXIT,
        263: 'back',
    },
    Mode.INSERT: {
        **ORD2CHAR,
        27: Mode.NORMAL,
    },
}

DISCOVER_GROUP = ('239.255.255.250', 1900)

DISCOVER_MESSAGE = '''\
M-SEARCH * HTTP/1.1\r\n\
Host: {}:{}\r\n\
Man: "ssdp:discover"\r\n\
ST: roku:ecp\r\n\r\n\
'''.format(*DISCOVER_GROUP)


def find_roku():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(DISCOVER_MESSAGE.encode(), DISCOVER_GROUP)
    data = s.recv(1024)
    s.close()
    return data.decode()


def keypress(url, key):
    if key is None:
        return
    if key in [*string.ascii_lowercase, ['%20']]:
        key = 'lit_' + key
    request_url = url + 'keypress/' + key
    resp = requests.post(request_url, timeout=10)
    if resp.status_code != 200:
        logger.error('Problem communicating with Roku')


class HTTPResponse:
    def __init__(self, response_text):

        response = response_text.split('\r\n')
        status_line = response[0].split()

        self.http_version = status_line[0]
        self.status_code = status_line[1]
        self.status = status_line[2]
        self.headers = {}

        for line in response[1:]:
            line = line.split()
            if len(line) == 2:
                header_name = line[0][:-1]
                header_value = line[1]
                self.headers[header_name.lower()] = header_value.lower()


def draw_insert_mode(stdscr):
    stdscr.addstr(1, 0, 'back to normal mode: esc')


def draw_normal_mode(stdscr):
    stdscr.addstr(1, 0, 'insert mode: `i`')
    stdscr.addstr(2, 0, '   /^\\        n|J -> volume down')
    stdscr.addstr(3, 0, '    k          m|K -> volume up')
    stdscr.addstr(4, 0, '<h  *  l>      b   -> volume mute')
    stdscr.addstr(5, 0, '    j')
    stdscr.addstr(6, 0, '   \\./')


def draw(mode, stdscr):
    stdscr.erase()
    if mode == Mode.NORMAL:
        draw_normal_mode(stdscr)
    elif mode == Mode.INSERT:
        draw_insert_mode(stdscr)
    stdscr.addstr(7, 0, 'input: ')
    stdscr.refresh()


@contextmanager
def scr():
    try:
        yield curses.initscr()
    finally:
        curses.endwin()


@dataclass
class Roku:
    location: str
    mode: Mode = Mode.NORMAL

    @classmethod
    def find(cls):
        logger.info('Searching for a Roku device...')
        response_text = find_roku()
        response = HTTPResponse(response_text)
        location = response.headers['location']
        return cls(location=location)

    def act(self, action):
        if isinstance(action, Mode):
            if action == Mode.EXIT:
                return
            self.mode = action
        keypress(self.location, action)

    def run(self, *, debug=False):
        with scr() as stdscr:
            stdscr.keypad(True)
            draw(self.mode, stdscr)
            while key := stdscr.getch():
                action = KEYPRESS_MAP[self.mode].get(key)
                self.act(action)
                draw(self.mode, stdscr)
                if debug:
                    stdscr.addstr(8, 0, f'   key pressed: {key} --> {action}')
