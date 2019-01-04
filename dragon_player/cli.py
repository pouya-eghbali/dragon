from asciimatics.screen import Screen
from time import sleep
import re, os, sys
from dragon_player.youtube_api import do_search
import os.path, json
from dragon_player.decorators import run_async
import vlc, json, subprocess
from youtube_dl import YoutubeDL

def download(url, dragon, on_dl_completed, print_dl_progress):
    dragon.print_dl_message('Getting streams...')
    def my_hook(d):
        if d['status'] == 'finished':
            on_dl_completed()
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(os.path.expanduser('~/Dragon'), '%(id)s'),
        'noplaylist' : True,
        'postprocessors': [],
        'progress_hooks': [my_hook],
        }
    ydl = YoutubeDL(ydl_opts)
    meta = ydl.extract_info(url, download=False)
    dragon.yt_title = meta['title']
    dragon.print_dl_message('Downloading stream...')
    yt = ydl.download([url])
    #dragon.print_dl_message('Converting file...')
    #convert(os.path.expanduser(f'~/Dragon/{dragon.yid}'), os.path.expanduser(f'~/Dragon/{dragon.yid}.aac'))
    #os.remove(os.path.expanduser(f'~/Dragon/{dragon.yid}'))
    #dragon.print_dl_message('Finished processing.')

class dragon(object):
    def __init__(self, screen, fps = 120):
        self.version = '0.6'
        self.screen = screen
        self.cmd = ''
        self.fps = fps
        self.command = ''
        self.dl_list = []
        self.media_dir = '~/Dragon'
        self.mediaplayer = vlc.MediaPlayer()
        self.curr_song = None
        self.media_name = None
        self.yid = None
        self.dl_percentage = 0
        self.repeat = False
        self.continuous = True
        self.looping = True
        self.playing = False
        self.pl_highlight_index = 0
        with open(os.path.expanduser('~/Dragon/main.json'), 'r', encoding='utf-8') as f:
            self.playlist = list(enumerate(json.load(f)))
            self.pl_index = len(self.playlist)
            if self.pl_index > 2:
                self.pl_index = 2
            self.pl_name = 'main'
        self.run_forever()

    def ms_to_human(self, ms):
        ts = int(ms / 1000)
        hours = int(ts / (60 * 60))
        minutes = int((ts - (hours * 60 * 60)) / 60)
        seconds = int((ts - (hours * 60 * 60) - (minutes * 60)))
        return f'{hours}:{minutes}:{seconds}'

    def process_events(self):
        event = self.screen.get_event()
        if event and hasattr(event, 'key_code'):
            key_code = event.key_code
            if key_code == -300: #back
                self.screen.print_at(' '*len(self.cmd), 6, 16)
                self.cmd = self.cmd[:-1]
            elif key_code in [10, 13]: #return
                if not self.cmd:
                    if self.pl_highlight_index == self.curr_song and self.mediaplayer.is_playing():
                        self.playing = False
                        self.mediaplayer.pause()
                    elif self.pl_highlight_index == self.curr_song and not self.mediaplayer.is_playing():
                        self.playing = True
                        self.mediaplayer.play()
                    else:
                        self.playing = False
                        self.mediaplayer.pause()
                        self.play_from_list(self.pl_highlight_index)
                else:
                    command = self.cmd
                    self.screen.print_at(' '*len(self.cmd), 6, 16)
                    self.screen.refresh()
                    self.cmd = ''
                    self.run_cmd(command)
            elif key_code == -204: #up
                self.pl_highlight_index -= 1
                self.print_playlist(self.pl_index - 1)
            elif key_code == -206: #down
                self.pl_highlight_index += 1
                self.print_playlist(self.pl_index + 1)
            else:
                try:
                    self.cmd += chr(key_code)
                except Exception as e:
                    pass

    def print_media(self):
        self.clear_line(14)
        if self.mediaplayer.is_playing():
            now   = self.ms_to_human(self.mediaplayer.get_time())
            total = self.ms_to_human(self.mediaplayer.get_length())
            self.screen.print_at(' '*self.screen.width, 0, 14)
            self.screen.print_at(f'{self.media_name} - {now} of {total}', 4, 14)
            self.screen.set_title(f'Dragon Player - {self.media_name}')

    def play_from_list(self, index):
        try:
            i, item = self.playlist[index]
            fname = item['file']
            fpath = os.path.expanduser(f'~/Dragon/{fname}')
            self.media_name = item['title']
            self.move_off_canvas()
            self.mediaplayer.pause()
            self.mediaplayer.set_mrl(fpath)
            self.mediaplayer.play()
            while not self.mediaplayer.is_playing():
                sleep(0.01)
            self.curr_song = index
            self.playing = True
        except Exception as e:
            self.print_status_message('Item not found on list')

    def reload_playlist(self):
        try:
            with open(os.path.expanduser(f'~/Dragon/{self.pl_name}.json'), 'r', encoding='utf-8') as f:
                self.playlist = list(enumerate(json.load(f)))
        except Exception as e:
            self.print_status_message('Error loading playlist')
        self.print_playlist(self.pl_index)

    #@run_async
    def run_cmd(self, cmd):
        if re.match(r'^(p|pause)$', cmd):
            self.mediaplayer.pause()
            self.playing = False
        elif re.match(r'^(e|exit)$', cmd):
            sys.exit(0)
        elif re.match(r'^(s|sc|scroll) ([0-9]+)$', cmd):
            command, query = re.match(r'([^ ]+) ?(.*)?', cmd).groups()
            self.pl_highlight_index = int(query)
            self.print_playlist(int(query))
        elif re.match(r'^(f|s|find|search) (.+)$', cmd):
            command, query = re.match(r'([^ ]+) ?(.*)?', cmd).groups()
            self.dl_list = do_search(query)
            self.print_dl_list()
        elif re.match(r'^(m|ml|mkl|mk list|make list) (.+)$', cmd):
            command, query = re.match(r'([^ ]+) ?(.*)?', cmd).groups()
            try:
                with open(os.path.expanduser(f'~/Dragon/{query}.json'), 'r', encoding='utf-8') as f:
                    self.print_status_message('Playlist already exists')
            except Exception as e:
                with open(os.path.expanduser(f'~/Dragon/{query}.json'), 'w', encoding='utf-8') as f:
                    json.dump([], f, indent='  ')
                self.print_status_message('Playlist created')
        elif re.match(r'^(dup|duplicate|duplicate list|dupl) (.+)$', cmd):
            command, query = re.match(r'([^ ]+) ?(.*)?', cmd).groups()
            try:
                with open(os.path.expanduser(f'~/Dragon/{query}.json'), 'r', encoding='utf-8') as f:
                    self.print_status_message('Playlist already exists')
            except Exception as e:
                with open(os.path.expanduser(f'~/Dragon/{query}.json'), 'w', encoding='utf-8') as f:
                    json.dump([i[1] for i in self.playlist], f, indent='  ')
                self.print_status_message('Playlist duplicated')
        elif re.match(r'^(srt|sort list|sort)$', cmd):
            playlist = [i[1] for i in self.playlist]
            sorted_pl = list(sorted(playlist, key = lambda i: i['title']))
            try:
                with open(os.path.expanduser(f'~/Dragon/{self.pl_name}.json'), 'w', encoding='utf-8') as f:
                    json.dump(sorted_pl, f, indent='  ')
                    self.playlist = list(enumerate(sorted_pl))
                    self.print_playlist(self.pl_index)
            except Exception as e:
                self.print_status_message('Sort failed')
        elif re.match(r'^(rml|rl|remove list|rm list) (.+)$', cmd):
            command, query = re.match(r'([^ ]+) ?(.*)?', cmd).groups()
            try:
                os.remove(os.path.expanduser(f'~/Dragon/{query}.json'))
                self.print_status_message('Playlist removed')
            except Exception as e:
                self.print_status_message('Cannot remove playlist')
        elif re.match(r'^(a|add|add to list|atl) ([0-9]+) (.+)$', cmd):
            command, index, query = re.match(r'([^ ]+) ([0-9]+) (.+)$', cmd).groups()
            index = int(index)
            item = self.playlist[index][1]
            try:
                with open(os.path.expanduser(f'~/Dragon/{query}.json'), 'r', encoding='utf-8') as f:
                    playlist = json.load(f)
                playlist.append(item)
                with open(os.path.expanduser(f'~/Dragon/{query}.json'), 'w', encoding='utf-8') as f:
                    json.dump(playlist, f, indent='  ')
                self.print_status_message('Item added to list')
            except Exception as e:
                self.print_status_message('Playlist not found')
        elif re.match(r'^(rename|rn) ([0-9]+) (.+)$', cmd):
            command, index, query = re.match(r'([^ ]+) ([0-9]+) (.+)$', cmd).groups()
            index = int(index)
            self.playlist[index][1]['title'] = query
            try:
                with open(os.path.expanduser(f'~/Dragon/{self.pl_name}.json'), 'w', encoding='utf-8') as f:
                    json.dump([i[1] for i in self.playlist], f, indent='  ')
                self.print_status_message('Item renamed')
                self.reload_playlist()
            except Exception as e:
                self.print_status_message('Could not rename')
        elif re.match(r'^(r|rfl|remove|remove from list) ([0-9]+)$', cmd):
            command, index = re.match(r'([^ ]+) ([0-9]+)$', cmd).groups()
            index = int(index)
            self.playlist.remove(index)
            try:
                with open(os.path.expanduser(f'~/Dragon/{self.pl_name}.json'), 'w', encoding='utf-8') as f:
                    json.dump([i[1] for i in self.playlist], f, indent='  ')
                self.print_status_message('Item removed from list')
                self.reload_playlist()
            except Exception as e:
                self.print_status_message('Failed to remove')
        elif re.match(r'^(p|play) ([0-9]+)$', cmd):
            command, query = re.match(r'([^ ]+) ?(.*)?', cmd).groups()
            query = int(query)
            self.playing = False
            self.mediaplayer.pause()
            self.play_from_list(query)
        elif re.match(r'^(b|prev)', cmd):
            self.playing = False
            self.mediaplayer.pause()
            self.play_from_list(self.curr_song - 1)
        elif re.match(r'^(n|next)', cmd):
            self.playing = False
            self.mediaplayer.pause()
            self.play_from_list(self.curr_song + 1)
        elif re.match(r'^(r|repeat)$', cmd):
            self.repeat = not self.repeat
        elif re.match(r'^(c|continuous)$', cmd):
            self.continuous = not self.continuous
        elif re.match(r'^(l|loop)$', cmd):
            self.looping = not self.looping
        elif re.match(r'^(\+|-) ?([0-9]+)$', cmd):
            sign, n = re.match(r'^(\+|-) ?([0-9]+)$', cmd).groups()
            now = self.mediaplayer.get_time()
            new = int(now + (int(f'{sign}{n}') * 1000))
            self.playing = False
            self.move_off_canvas()
            self.mediaplayer.set_time(new)
            self.playing = True
        elif re.match(r'^(\+|-) ?([0-9]+) ?(s|m|h)$', cmd):
            sign, n, t = re.match(r'^(\+|-) ?([0-9]+) ?(s|m|h)$', cmd).groups()
            now = self.mediaplayer.get_time()
            t = ({'s': 1000, 'm': 60 * 1000, 'h': 60 * 60 * 1000})[t]
            new = int(now + (int(f'{sign}{n}') * t))
            self.playing = False
            self.move_off_canvas()
            self.mediaplayer.set_time(new)
            self.playing = True
        elif re.match(r'^(l|load) (.+)$', cmd):
            command, query = re.match(r'([^ ]+) ?(.*)?', cmd).groups()
            try:
                with open(os.path.expanduser(f'~/Dragon/{query}.json'), 'r', encoding='utf-8') as f:
                    self.playlist = list(enumerate(json.load(f)))
                    self.pl_name = query
            except Exception as e:
                self.print_status_message('Error loading playlist')
            self.print_playlist()
        elif re.match(r'^(d|dl|download) ([0-9]+)$', cmd):
            command, query = re.match(r'([^ ]+) ?(.*)?', cmd).groups()
            self.command = 'download'
            index = int(query)
            self.yid = self.dl_list[index][1]
            url = f'http://www.youtube.com/watch?v={self.yid}'
            download(url, self, self.on_dl_completed, self.print_dl_progress)
        pass

    def on_dl_completed(self):
        self.print_dl_message('Adding to main playlist...')
        with open(os.path.expanduser(f'~/Dragon/{self.pl_name}.json'), 'r', encoding = 'utf-8') as f:
            playlist = json.load(f)
        playlist.append({
            'file': f'{self.yid}',
            'yid': self.yid,
            'title': self.yt_title
        })
        with open(os.path.expanduser(f'~/Dragon/{self.pl_name}.json'), 'w', encoding = 'utf-8') as f:
            json.dump(playlist, f, indent='  ')
        self.print_dl_message('Download completed.')

    def print_dl_progress(self, stream, chunk, file_handle, bytes_remaining):
        total = stream.filesize
        downloaded = total - bytes_remaining
        percentage = int((downloaded / total) * 100)
        if (percentage != self.dl_percentage) or percentage == 0:
            self.dl_percentage = percentage
            self.print_dl_message(f'%{percentage} Downloaded')

    def clear_line(self, line):
        self.screen.print_at(' '*self.screen.width, 0, line)

    def print_dl_message(self, message):
        self.clear_line(15)
        self.screen.print_at(message, 4, 15)
        self.screen.refresh()

    def print_status_message(self, message):
        self.clear_line(15)
        self.screen.print_at(message, 4, 15)
        self.screen.refresh()

    def print_info(self):
        self.screen.print_at(f'Dragon YouTube Player CLI - v{self.version}', 4, 2)
        self.screen.print_at('By Pouya Eghbali', 4, 3)

    def move_off_canvas(self):
        self.screen.print_at(' ', 0, self.screen.height + 1)
        self.screen.refresh()

    def print_dl_list(self):
        if self.dl_list:
            for i in range(0, 5):
                self.clear_line(6+i)
            for i, item in enumerate(self.dl_list[:5]):
                self.screen.print_at(f'{i}: {item[0]}', 4, 6+i)

    def print_playlist(self, mid=2):
        if mid > len(self.playlist) - 3:
            mid = len(self.playlist) - 3
        if mid - 2 <= 0:
            mid = 2
        self.pl_index = mid
        start = mid - 2
        if start < 0: start = 0
        if self.pl_highlight_index >= len(self.playlist):
            self.pl_highlight_index = len(self.playlist) - 1
        if self.pl_highlight_index <= 0:
            self.pl_highlight_index = 0
        if self.playlist:
            for i in range(0, 5):
                self.clear_line(6+i)
            for i, item in self.playlist[start:start+5]:
                if i == self.pl_highlight_index:
                    self.screen.print_at(f' {i}: {item["title"]} ', 3, 6+i-start, colour=0, bg=6)
                else:
                    self.screen.print_at(f'{i}: {item["title"]}', 4, 6+i-start)

    def print_cmd(self):
        self.clear_line(16)
        self.screen.print_at('$ ', 4, 16)
        self.screen.print_at(self.cmd, 6, 16)

    def print_status(self):
        self.clear_line(13)
        status = []
        if self.repeat:
            status.append('[R]')
        else:
            status.append('R')
        if self.continuous:
            status.append('[C]')
        else:
            status.append('C')
        if self.looping:
            status.append('[L]')
        else:
            status.append('L')
        self.screen.print_at(' '.join(status), 4, 13)

    def draw_frame(self):
        self.process_events()
        self.screen.refresh()
        #sleep(1/self.fps)

    def if_play_next(self):
        if self.playing and self.continuous and not self.mediaplayer.is_playing():
            if not self.repeat:
                if self.curr_song + 1 == len(self.playlist):
                    if self.looping:
                        self.curr_song = -1
                    else:
                        self.playing = False
                        self.print_status_message('Reached end of the list')
                        return
                self.play_from_list(self.curr_song + 1)
            else:
                self.play_from_list(self.curr_song)

    def run_forever(self):
        self.screen.set_title(f'Dragon Player')
        self.print_info()
        self.print_playlist()
        while True:
            self.print_cmd()
            self.print_media()
            self.print_status()
            self.if_play_next()
            self.draw_frame()

def main():
    if 'termux' in os.path.expanduser('~/Dragon'):
        os.environ['HOME'] = '/mnt/ext_sdcard'

    try:
        os.mkdir(os.path.expanduser('~/Dragon'))
    except:
        pass
    try:
        with open(os.path.expanduser('~/Dragon/main.json'), 'r', encoding='utf-8') as f:
            pass
    except:
        with open(os.path.expanduser('~/Dragon/main.json'), 'w', encoding='utf-8') as f:
            json.dump([], f)

    Screen.wrapper(dragon)

if __name__ == '__main__':
    main()
