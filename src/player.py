#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: omi
# @Date:   2014-07-15 15:48:27
# @Last Modified by:   manfred
# @Last Modified time: 2014-08-25 18:02:00


'''
网易云音乐 Player
'''
# Let's make some noise
import random

import subprocess
import threading
import time
import os
import signal
from ui import Ui


# carousel x in [left, right]
carousel = lambda left, right, x: left if (x > right) else (right if x < left else x)


class Player:



    def __init__(self):
        self.ui = Ui()
        self.data_type = 'songs'
        self.popen_handler = None
        # flag stop, prevent thread start
        self.playing_flag = False
        self.pause_flag = False
        self.songs = []
        self.idx = 0
        self.play_mode = 'norm'

    def popen_recall(self, on_exit, popen_args):
        """
        Runs the given args in a subprocess.Popen, and then calls the function
        onExit when the subprocess completes.
        onExit is a callable object, and popenArgs is a lists/tuple of args that
        would give to subprocess.Popen.
        """

        def run_in_thread(on_exit, popen_args):
            self.popen_handler = subprocess.Popen(['mpg123', popen_args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE)
            self.popen_handler.wait()
            if self.playing_flag:
                self.idx = carousel(0, len(self.songs) - 1, self.idx + 1)
                on_exit()
            return

        thread = threading.Thread(target=run_in_thread, args=(on_exit, popen_args))
        thread.start()
        # returns immediately after the thread starts
        return thread

    def recall(self):
        self.playing_flag = True
        item = self.songs[self.idx]
        self.ui.build_playinfo(item['song_name'], item['artist'], item['album_name'], play_mode=self.play_mode)
        self.popen_recall(self.recall, item['mp3_url'])

    def play(self, datatype, songs, idx):
        # if same playlists && idx --> same song :: pause/resume it
        self.data_type = datatype

        if datatype == 'songs' or datatype == 'djchannels':
            if idx == self.idx and songs == self.songs:
                if self.pause_flag:
                    self.resume()
                else:
                    self.pause()

            else:
                if datatype == 'songs' or datatype == 'djchannels':
                    self.songs = songs
                    self.idx = idx

                # if it's playing
                if self.playing_flag:
                    self.switch()

                # start new play
                else:
                    self.recall()
        # if current menu is not song, pause/resume
        else:
            if self.playing_flag:
                if self.pause_flag:
                    self.resume()
                else:
                    self.pause()
            else:
                pass

    # play another
    def switch(self):
        self.stop()
        # wait process be killed
        time.sleep(0.01)
        self.recall()

    def stop(self):
        if self.playing_flag and self.popen_handler:
            self.playing_flag = False
            self.popen_handler.kill()

    def pause(self):
        self.pause_flag = True
        os.kill(self.popen_handler.pid, signal.SIGSTOP)
        item = self.songs[self.idx]
        self.ui.build_playinfo(item['song_name'], item['artist'], item['album_name'], pause=True, play_mode=self.play_mode)

    def resume(self):
        self.pause_flag = False
        os.kill(self.popen_handler.pid, signal.SIGCONT)
        item = self.songs[self.idx]
        self.ui.build_playinfo(item['song_name'], item['artist'], item['album_name'], play_mode=self.play_mode)

    def next(self):
        self.stop()
        time.sleep(0.01)
        if self.play_mode == 'rand':
            self.idx = random.randint(0, len(self.songs) - 1)
        elif self.play_mode == 'loop':
            self.idx = self.idx
        else:
            self.idx = carousel(0, len(self.songs) - 1, self.idx + 1)
        self.recall()

    def prev(self):
        self.stop()
        time.sleep(0.01)
        if self.play_mode == 'rand':
            self.idx = random.randint(0, len(self.songs) - 1)
        elif self.play_mode == 'loop':
            self.idx = self.idx
        else:
            self.idx = carousel(0, len(self.songs) - 1, self.idx - 1)
        self.recall()

    def next_play_mode(self):
        if len(self.songs) == 0:
            return

        if self.play_mode == 'norm':
            self.play_mode = 'rand'
        elif self.play_mode == 'rand':
            self.play_mode = 'loop'
        elif self.play_mode == 'loop':
            self.play_mode = 'norm'
        else:
            pass

        item = self.songs[self.idx]
        self.ui.build_playinfo(item['song_name'], item['artist'], item['album_name'], play_mode=self.play_mode)