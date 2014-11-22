#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: omi
# @Date:   2014-08-24 21:51:57
# @Last Modified by:   omi
# @Last Modified time: 2014-08-25 18:02:04


'''
网易云音乐 Menu
'''

import curses
import locale
import sys
import os
import json
import time
import webbrowser
from api import NetEase
from player import Player
from ui import Ui
from const import Constant
import logger

# expand the path of home-folder to full-length path
home = os.path.expanduser("~")
# if the config directory doesn't exists, then create a new one
if os.path.isdir(Constant.conf_dir) is False:
    os.mkdir(Constant.conf_dir)

locale.setlocale(locale.LC_ALL, "")
code = locale.getpreferredencoding()

# carousel x in [left, right]
carousel = lambda left, right, x: left if (x > right) else (right if x < left else x)

shortcut = [
    ['j', 'Down      ', '下移'],
    ['k', 'Up        ', '上移'],
    ['h', 'Back      ', '后退'],
    ['l', 'Forward   ', '前进'],
    ['u', 'Prev page ', '上一页'],
    ['d', 'Next page ', '下一页'],
    ['f', 'Search    ', '快速搜索'],
    ['[', 'Prev song ', '上一曲'],
    [']', 'Next song ', '下一曲'],
    [' ', 'Play/Pause', '播放/暂停'],
    ['m', 'Menu      ', '主菜单'],
    ['p', 'Present   ', '当前播放列表'],
    ['a', 'Add       ', '添加曲目到打碟'],
    ['z', 'DJ list   ', '打碟列表'],
    ['s', 'Star      ', '添加到收藏'],
    ['c', 'Collection', '收藏列表'],
    ['r', 'Remove    ', '删除当前条目'],
    ['q', 'Quit      ', '退出']
]

log = logger.getLogger(__name__)


class Menu:
    def __init__(self):
        reload(sys)
        sys.setdefaultencoding('UTF-8')
        self.data_type = 'main'
        # Title of the application
        self.title = '网易云音乐'
        # Main-menu list
        self.data_list = ['排行榜', '艺术家', '新碟上架', '精选歌单', '我的歌单', 'DJ节目', '打碟', '收藏', '搜索', '帮助']
        # Which page of the data_list is displayed (data_list may be displayed in multiple pages
        self.page_index = 0
        # The index of the current selected line
        self.current_line_index = 0
        self.present_songs = []
        self.player = Player()
        self.ui = Ui()
        self.netease = NetEase()
        self.screen = curses.initscr()
        self.screen.keypad(1)
        self.page_size = 10  # The number of lines that can be displayed on one page.
        self.stack = []
        self.dj_stack = []
        self.user_id = None
        self.user_name = None

        # Read in the collection and account in flavor.json
        try:
            config_file = file(Constant.conf_dir + "/flavor.json", 'r')
            data = json.loads(config_file.read())
            self.collection = data['collection']
            self.account = data['account']
            config_file.close()
        except:
            self.collection = []
            self.account = {}

    def start(self):
        # draw the main menu
        self.ui.build_menu(self.data_type, self.title, self.data_list, self.page_index, self.current_line_index, self.page_size)
        # push current menu into stack
        self.stack.append([self.data_type, self.title, self.data_list, self.page_index, self.current_line_index])

        # Main loop
        while True:
            # refresh the menu
            data_type = self.data_type
            title = self.title
            data_list = self.data_list
            page_index = self.page_index
            idx = current_line_index = self.current_line_index
            page_size = self.page_size
            stack = self.stack
            dj_stack = self.dj_stack
            self.ui.screen.refresh()




            # fetch a user's command
            key = self.screen.getch()
            # quit
            if key == ord('q'):
                break

            # move up
            elif key == ord('k') or key == curses.KEY_UP:
                self.current_line_index = carousel(page_index, min(len(data_list), page_index + page_size) - 1, idx - 1)
                # DEBUG
                # self.ui.screen.addstr(0, 0,'current_line_index: {}, begin: {}, end: {}'.format(self.current_line_index, page_index, min(len(data_list), page_index+page_size)))

            # move down
            elif key == ord('j') or key == curses.KEY_DOWN:
                self.current_line_index = carousel(page_index, min(len(data_list), page_index + page_size) - 1, idx + 1)
                # DEBUG
                # self.ui.screen.addstr(0, 0,'current_line_index: {}, begin: {}, end: {}'.format(self.current_line_index, page_index, min(len(data_list), page_index+page_size)))

            # number shortcut
            elif ord('0') <= key <= ord('9'):
                if self.data_type == 'songs' or self.data_type == 'djchannels' or self.data_type == 'help':
                    continue
                idx = key - ord('0')
                self.ui.build_menu(self.data_type, self.title, self.data_list, self.page_index, idx, self.page_size)
                self.ui.build_loading()
                self.dispatch_enter(idx)
                self.current_line_index = 0
                self.page_index = 0

                # 向上翻页
            elif key == ord('u') or key == curses.KEY_PPAGE:
                if page_index == 0:
                    continue
                self.page_index -= page_size

                # Move to first line of the page
                self.current_line_index = (current_line_index - page_size) // page_size * page_size

            # 向下翻页
            elif key == ord('d') or key == curses.KEY_NPAGE:
                if page_index + page_size >= len(data_list):
                    continue
                self.page_index += page_size

                # Move to first line of the page
                self.current_line_index = (current_line_index + page_size) // page_size * page_size

            # 前进
            elif key == ord('l') or key == 10 or key == curses.KEY_RIGHT:
                if self.data_type == 'songs' or self.data_type == 'djchannels' or self.data_type == 'help':
                    continue
                self.ui.build_loading()
                self.dispatch_enter(idx)
                self.current_line_index = 0
                self.page_index = 0

                # 回退
            elif key == ord('h') or key == curses.KEY_LEFT:
                # if not main menu
                if len(self.stack) == 1:
                    continue
                last_menu = stack.pop()
                self.data_type = last_menu[0]
                self.title = last_menu[1]
                self.data_list = last_menu[2]
                self.page_index = last_menu[3]
                self.current_line_index = last_menu[4]

            # 搜索
            elif key == ord('f'):
                self.search()

            # 播放下一曲
            elif key == ord(']') or key == curses.KEY_NEXT:
                if len(self.present_songs) == 0:
                    continue
                self.player.next()
                time.sleep(0.1)

            # 播放上一曲
            elif key == ord('[') or key == curses.KEY_PREVIOUS:
                if len(self.present_songs) == 0:
                    continue
                self.player.prev()
                time.sleep(0.1)

            # 播放、暂停
            elif key == ord(' '):
                if data_type == 'songs':
                    self.present_songs = ['songs', title, data_list, page_index, current_line_index]
                elif data_type == 'djchannels':
                    self.present_songs = ['djchannels', title, data_list, page_index, current_line_index]
                self.player.play(data_type, data_list, idx)
                time.sleep(0.1)

            # 加载当前播放列表
            elif key == ord('p'):
                if len(self.present_songs) == 0:
                    continue
                self.stack.append([data_type, title, data_list, page_index, current_line_index])
                self.data_type = self.present_songs[0]
                self.title = self.present_songs[1]
                self.data_list = self.present_songs[2]
                self.page_index = self.present_songs[3]
                self.current_line_index = self.present_songs[4]

            # 添加到打碟歌单
            elif key == ord('a'):
                if data_type == 'songs' and len(data_list) != 0:
                    self.dj_stack.append(data_list[idx])
                elif data_type == 'artists':
                    pass

            # 加载打碟歌单
            elif key == ord('z'):
                self.stack.append([data_type, title, data_list, page_index, current_line_index])
                self.data_type = 'songs'
                self.title = '网易云音乐 > 打碟'
                self.data_list = self.dj_stack
                self.page_index = 0
                self.current_line_index = 0

            # 添加到收藏歌曲
            elif key == ord('s'):
                if (data_type == 'songs' or data_type == 'djchannels') and len(data_list) != 0:
                    self.collection.append(data_list[idx])

            # 加载收藏歌曲
            elif key == ord('c'):
                self.stack.append([data_type, title, data_list, page_index, current_line_index])
                self.data_type = 'songs'
                self.title = '网易云音乐 > 收藏'
                self.data_list = self.collection
                self.page_index = 0
                self.current_line_index = 0

            # 从当前列表移除
            elif key == ord('r'):
                if data_type != 'main' and len(data_list) != 0:
                    self.data_list.pop(idx)
                    self.current_line_index = carousel(page_index, min(len(data_list), page_index + page_size) - 1, idx)

            elif key == ord('m'):
                if data_type != 'main':
                    self.stack.append([data_type, title, data_list, page_index, current_line_index])
                    self.data_type = self.stack[0][0]
                    self.title = self.stack[0][1]
                    self.data_list = self.stack[0][2]
                    self.page_index = 0
                    self.current_line_index = 0

            elif key == ord('g'):
                if data_type == 'help':
                    webbrowser.open_new_tab('https://github.com/darknessomi/musicbox')

            elif key == ord('\\'):
                self.player.next_play_mode()

            # refresh the window
            self.ui.build_menu(self.data_type, self.title, self.data_list, self.page_index, self.current_line_index, self.page_size)

        self.player.stop()
        sfile = file(Constant.conf_dir + "/flavor.json", 'w')
        data = {
            'account': self.account,
            'collection': self.collection
        }
        sfile.write(json.dumps(data))
        sfile.close()
        curses.endwin()

    def dispatch_enter(self, idx):
        # The end of stack
        netease = self.netease
        datatype = self.data_type
        title = self.title
        datalist = self.data_list
        offset = self.page_index
        index = self.current_line_index
        self.stack.append([datatype, title, datalist, offset, index])

        if datatype == 'main':
            self.choice_channel(idx)

            # 该艺术家的热门歌曲
        elif datatype == 'artists':
            artist_id = datalist[idx]['artist_id']
            songs = netease.artists(artist_id)
            self.data_type = 'songs'
            self.data_list = netease.dig_info(songs, 'songs')
            self.title += ' > ' + datalist[idx]['artists_name']

        # 该专辑包含的歌曲
        elif datatype == 'albums':
            album_id = datalist[idx]['album_id']
            songs = netease.album(album_id)
            self.data_type = 'songs'
            self.data_list = netease.dig_info(songs, 'songs')
            self.title += ' > ' + datalist[idx]['albums_name']

        # 精选歌单选项
        elif datatype == 'playlists':
            data = self.data_list[idx]
            self.data_type = data['datatype']
            self.data_list = netease.dig_info(data['callback'](), self.data_type)
            self.title += ' > ' + data['title']

        # 全站置顶歌单包含的歌曲
        elif datatype == 'top_playlists':
            log.debug(datalist)
            playlist_id = datalist[idx]['playlist_id']
            songs = netease.playlist_detail(playlist_id)
            self.data_type = 'songs'
            self.data_list = netease.dig_info(songs, 'songs')
            self.title += ' > ' + datalist[idx]['playlists_name']

        # 分类精选
        elif datatype == 'playlist_classes':
            # 分类名称
            data = self.data_list[idx]
            self.data_type = 'playlist_class_detail'
            self.data_list = netease.dig_info(data, self.data_type)
            self.title += ' > ' + data
            log.debug(self.data_list)

        # 某一分类的详情
        elif datatype == 'playlist_class_detail':
            # 子类别
            data = self.data_list[idx]
            self.data_type = 'top_playlists'
            self.data_list = netease.dig_info(netease.top_playlists(data), self.data_type)
            log.debug(self.data_list)
            self.title += ' > ' + data

    def choice_channel(self, idx):
        # 排行榜
        netease = self.netease
        if idx == 0:
            songs = netease.top_songlist()
            self.data_list = netease.dig_info(songs, 'songs')
            self.title += ' > 排行榜'
            self.data_type = 'songs'

        # 艺术家
        elif idx == 1:
            artists = netease.top_artists()
            self.data_list = netease.dig_info(artists, 'artists')
            self.title += ' > 艺术家'
            self.data_type = 'artists'

        # 新碟上架
        elif idx == 2:
            albums = netease.new_albums()
            self.data_list = netease.dig_info(albums, 'albums')
            self.title += ' > 新碟上架'
            self.data_type = 'albums'

        # 精选歌单
        elif idx == 3:
            self.data_list = [
                {
                    'title': '全站置顶',
                    'datatype': 'top_playlists',
                    'callback': netease.top_playlists
                },
                {
                    'title': '分类精选',
                    'datatype': 'playlist_classes',
                    'callback': netease.playlist_classes
                }
            ]
            self.title += ' > 精选歌单'
            self.data_type = 'playlists'

        # 我的歌单
        elif idx == 4:
            # 未登录
            if self.user_id is None:
                # 使用本地存储了账户登录
                if self.account:
                    user_info = netease.login(self.account[0], self.account[1])
                else:
                    user_info = {}

                # 本地没有存储账户，或本地账户失效，则引导录入
                # if self.account == {} or user_info['code'] != 200:
                if self.account == {} or user_info['code'] != 200:
                    data = self.ui.build_login()
                    # 取消登录
                    if data == -1:
                        return
                    user_info = data[0]
                    self.account = data[1]

                self.user_name = user_info['profile']['nickname']
                self.user_id = user_info['account']['id']

            # 读取登录之后的用户歌单
            myplaylist = netease.user_playlist(self.user_id)
            self.data_type = 'top_playlists'
            self.data_list = netease.dig_info(myplaylist, self.data_type)
            self.title += ' > ' + self.user_name + ' 的歌单'

        # DJ节目
        elif idx == 5:
            self.data_type = 'djchannels'
            self.title += ' > DJ节目'
            self.data_list = netease.djchannels()

        # 打碟
        elif idx == 6:
            self.data_type = 'songs'
            self.title += ' > 打碟'
            self.data_list = self.dj_stack

        # 收藏
        elif idx == 7:
            self.data_type = 'songs'
            self.title += ' > 收藏'
            self.data_list = self.collection

        # 搜索
        elif idx == 8:
            self.search()

        # 帮助
        elif idx == 9:
            self.data_type = 'help'
            self.title += ' > 帮助'
            self.data_list = shortcut

        self.page_index = 0
        self.current_line_index = 0

    def search(self):
        ui = self.ui
        x = ui.build_search_menu()
        # if do search, push current info into stack
        if x in range(ord('1'), ord('5')):
            self.stack.append([self.data_type, self.title, self.data_list, self.page_index, self.current_line_index])
            self.current_line_index = 0
            self.page_index = 0

        if x == ord('1'):
            self.data_type = 'songs'
            self.data_list = ui.build_search('songs')
            self.title = '歌曲搜索列表'

        elif x == ord('2'):
            self.data_type = 'artists'
            self.data_list = ui.build_search('artists')
            self.title = '艺术家搜索列表'

        elif x == ord('3'):
            self.data_type = 'albums'
            self.data_list = ui.build_search('albums')
            self.title = '专辑搜索列表'

        elif x == ord('4'):
            # 搜索结果可以用top_playlists处理
            self.data_type = 'top_playlists'
            self.data_list = ui.build_search('search_playlist')
            self.title = '精选歌单搜索列表'
