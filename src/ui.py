#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: omi
# @Date:   2014-08-24 21:51:57
# @Last Modified by:   omi
# @Last Modified time: 2014-08-25 18:02:01


'''
网易云音乐 Ui
'''

import curses
import getpass
from api import NetEase


class Ui:
    def __init__(self):
        # Initializing curses
        # initialize window object to curses.initscr()
        self.screen = curses.initscr()
        # character break buffer, to read in any key without the need to press 'Enter'.
        curses.cbreak()
        # make those navigation keys to normal key that can be processed in program.
        self.screen.keypad(1)
        #   initialize the some color pair
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)


        # Initializing NetEase object to communicate with NetEase server.
        self.netease = NetEase()


    def build_playinfo(self, song_name, artist, album_name, pause=False, play_mode='normal'):
        curses.noecho()
        # refresh top 2 line
        self.screen.move(1, 1)
        self.screen.clrtoeol()
        self.screen.move(2, 1)
        self.screen.clrtoeol()
        if pause:
            self.screen.addstr(1, 0, play_mode + '  ' + '_ _ z Z Z', curses.color_pair(3))
        else:
            self.screen.addstr(1, 0, play_mode + '  ' + '♫  ♪ ♫  ♪', curses.color_pair(3))
        self.screen.addstr(1, 19, song_name + '   -   ' + artist + '  < ' + album_name + ' >', curses.color_pair(4))
        self.screen.refresh()

    def build_loading(self):
        self.screen.addstr(6, 19, '享受高品质音乐，loading...', curses.color_pair(1))
        self.screen.refresh()

    # draw the all types of menu according to data_type
    def build_menu(self, data_type, title, data_list, offset, index, step):
        # keep playing info in line 1

        # do not echo the input key-code
        curses.noecho()
        # clear the content after (4,1)
        # move cursor to (4,1)
        self.screen.move(4, 1)
        # clear the content under line-4, erase from cursor to the end of the window: all lines below the cursor are deleted,
        #  and then the equivalent of clrtoeol() is performed.
        self.screen.clrtobot()
        # draw the title with color pair 1 (GREEN, BLACK)
        self.screen.addstr(4, 19, title, curses.color_pair(1))

        # If there's nothing in the data_list
        if len(data_list) == 0:
            self.screen.addstr(8, 19, '这里什么都没有 -，-')

        else:
            if data_type == 'main':

                for i in range(offset, min(len(data_list), offset + step)):
                    content = str(i) + '. ' + data_list[i]
                    self.print_menu_line(i, offset, content, i == index)

            elif data_type == 'songs':
                for i in range(offset, min(len(data_list), offset + step)):
                    content = str(i) + '. ' + data_list[i]['song_name'] \
                              + '   -   ' + data_list[i]['artist'] + '  < ' + data_list[i]['album_name'] + ' >'
                    self.print_menu_line(i, offset, content, i == index)

            elif data_type == 'artists':
                for i in range(offset, min(len(data_list), offset + step)):
                    content = str(i) + '. ' + data_list[i]['artists_name'] + '   -   ' + str(data_list[i]['alias'])
                    self.print_menu_line(i, offset, content, i == index)


            elif data_type == 'albums':
                for i in range(offset, min(len(data_list), offset + step)):
                    content = str(i) + '. ' + data_list[i]['albums_name'] + '   -   ' + data_list[i]['artists_name']
                    self.print_menu_line(i, offset, content, i == index)

            elif data_type == 'playlists':
                for i in range(offset, min(len(data_list), offset + step)):
                    content = str(i) + '. ' + data_list[i]['title']
                    self.print_menu_line(i, offset, content, i == index)

            elif data_type == 'top_playlists':
                for i in range(offset, min(len(data_list), offset + step)):
                    content = str(i) + '. ' + data_list[i]['playlists_name'] + '   -   ' + data_list[i]['creator_name']
                    self.print_menu_line(i, offset, content, i == index)

            elif data_type == 'playlist_classes' or data_type == 'playlist_class_detail':
                for i in range(offset, min(len(data_list), offset + step)):
                    content = str(i) + '. ' + data_list[i]
                    self.print_menu_line(i, offset, content, i == index)

            elif data_type == 'djchannels':
                for i in range(offset, min(len(data_list), offset + step)):
                    content = str(i) + '. ' + data_list[i]['song_name']
                    self.print_menu_line(i, offset, content, i == index)

            elif data_type == 'help':
                for i in range(offset, min(len(data_list), offset + step)):
                    content = str(i) + '. \'' + data_list[i][0].upper() + '\'   ' + data_list[i][1] + '   ' + \
                              data_list[i][2]
                    self.print_menu_line(i, offset, content, i == index)
                self.screen.addstr(20, 6, 'NetEase-MusicBox 基于Python，所有版权音乐来源于网易，本地不做任何保存')
                self.screen.addstr(21, 10, '按 [G] 到 Git-hub 了解更多信息，帮助改进，或者Star表示支持~~')
                self.screen.addstr(22, 19, 'Build with love to music by omi')

        self.screen.refresh()

    # print the specified line at certain place
    def print_menu_line(self, i, offset, content, chosen=False):
        y = i - offset + 8

        if chosen == True:
            x = 16
            color = curses.color_pair(2)
            self.screen.addstr(y, x, '-> ' + content, color)
        else:
            x = 19
            self.screen.addstr(y, x, content)

    def build_search(self, stype):
        netease = self.netease
        if stype == 'songs':
            song_name = self.get_param('搜索歌曲：')
            try:
                data = netease.search(song_name, stype=1)
                song_ids = []
                if 'songs' in data['result']:
                    if 'mp3Url' in data['result']['songs']:
                        songs = data['result']['songs']

                    # if search song result do not has mp3Url
                    # send ids to get mp3Url
                    else:
                        for i in range(0, len(data['result']['songs'])):
                            song_ids.append(data['result']['songs'][i]['id'])
                        songs = netease.songs_detail(song_ids)
                    return netease.dig_info(songs, 'songs')
            except:
                return []

        elif stype == 'artists':
            artist_name = self.get_param('搜索艺术家：')
            try:
                data = netease.search(artist_name, stype=100)
                if 'artists' in data['result']:
                    artists = data['result']['artists']
                    return netease.dig_info(artists, 'artists')
            except:
                return []

        elif stype == 'albums':
            artist_name = self.get_param('搜索专辑：')
            try:
                data = netease.search(artist_name, stype=10)
                if 'albums' in data['result']:
                    albums = data['result']['albums']
                    return netease.dig_info(albums, 'albums')
            except:
                return []

        elif stype == 'search_playlist':
            artist_name = self.get_param('搜索网易精选集：')
            try:
                data = netease.search(artist_name, stype=1000)
                if 'playlists' in data['result']:
                    playlists = data['result']['playlists']
                    return netease.dig_info(playlists, 'top_playlists')
            except:
                return []

        return []

    def build_search_menu(self):
        self.screen.move(4, 1)
        self.screen.clrtobot()
        self.screen.addstr(8, 19, '选择搜索类型:', curses.color_pair(1))
        self.screen.addstr(10, 19, '[1] 歌曲')
        self.screen.addstr(11, 19, '[2] 艺术家')
        self.screen.addstr(12, 19, '[3] 专辑')
        self.screen.addstr(13, 19, '[4] 网易精选集')
        self.screen.addstr(16, 19, '请键入对应数字:', curses.color_pair(2))
        self.screen.refresh()
        x = self.screen.getch()
        return x

    # build login interface and login
    def build_login(self):
        curses.noecho()
        info = self.get_param('请输入登录信息， e.g: john_smith@gmail.com 123456')
        account = info.split(' ')
        # if both user-name and password is got.
        if len(account) != 2:
            return self.build_login()
        # login
        login_info = self.netease.login(account[0], account[1])
        self.screen.refresh()

        # if login successfully
        if login_info['code'] != 200:
            x = self.build_login_error()
            if x == ord('1'):
                return self.build_login()
            else:
                return -1
        else:
            return [login_info, account]

    def build_login_error(self):
        self.screen.move(4, 1)
        self.screen.clrtobot()
        self.screen.addstr(8, 19, '艾玛，登录信息好像不对呢 (O_O)#', curses.color_pair(1))
        self.screen.addstr(10, 19, '[1] 再试一次')
        self.screen.addstr(11, 19, '[2] 稍后再试')
        self.screen.addstr(14, 19, '请键入对应数字:', curses.color_pair(2))
        self.screen.refresh()
        x = self.screen.getch()
        return x

    def get_param(self, prompt_string):
        # When getting the user-name and password, we need to echo the letter user typed in.
        curses.echo()
        # clear the content after the 4th line
        self.screen.move(4, 1)
        self.screen.clrtobot()
        # print and display the prompt message to input user-name
        self.screen.addstr(5, 19, prompt_string, curses.color_pair(1))
        self.screen.addstr(9, 19, "Please input the user-name: ")
        self.screen.refresh()
        info = self.screen.getstr(10, 19, 60)

        # print the prompt to enter password
        self.screen.move(11, 19)
        # close curses mode to get password without display it
        self.end_curses()
        info = info + " " + getpass.getpass('                   Password:')
        self.start_curses()
        self.redraw()

        if info.strip() is '':
            return self.get_param(prompt_string)
        else:
            return info

    def start_curses(self):
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(1)

    def end_curses(self):
        curses.nocbreak()
        self.screen.keypad(0)
        curses.echo()

    def redraw(self):
        self.screen.clear()
        self.screen.addstr(4, 19, '网易云音乐', curses.color_pair(1))
        self.screen.refresh()