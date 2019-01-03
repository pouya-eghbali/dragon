
# Dragon

Dragon is a CLI YouTube music player app. This is for personal use only. I'm not responsible for any copyright related issues.

![Dragon Screenshot](https://github.com/pouya-eghbali/dragon/raw/master/dragon.png)

## Installation

Dragon is hosted on PyPI, to install do

	pip install dragon-player

Dragon requires libVLC to run. To run dragon do

	dragon

 It _should_ work on Linux, Mac, Windows and BSD

## Commands

Dragon supports the following text based commands:

|Command| Aliases | Argument| Example | Description
|--|--|--|--|--|
| search | find, s, f | text: song title | s metallica one	 | search for a song on YouTube |
| download | dl, d | number: index | dl 1 | download nth index from search results
| play | p | number: index | p 0 | play nth index in loaded playlist
| pause | p | | p | pause
| next | n | | n | play next track
| prev | b | | b | play previous track
| repeat | r | | r | repeat the current track
| continuous | c | | c | continue playing next track after current one is finished
| loop | l | | l | loop the playlist
| + | | time | `+1m` or `+1s` or `+1h` or `+1` | go forward
| - | | time | `-1m` or `-1s` or `-1h` or `-1` | go backward
| scroll | s, sc | number | sc 4 | scroll to number
| load | l | text: playlist name | load main | load playlist from disk
| make list | mk list, mkl, ml, m | text: playlist name | mkl heavy metal | make an empty new playlist
| duplicate list | duplicate, dupl, dup | text: playlist name | dup classical | duplicate current loaded playlist
| sort list | srt, sort | | sort | sort current loaded playlist
| remove list | rm list, rl, rml | text: playlist name | rm classical | remove playlist
| add to list | atl, add, a | number: index and text: playlist name | atl 1 heavy metal | add index from current list to another playlist
| remove from list | remove, rfl, r | number:index | r 1 | remove song from current playlist
| rename | rn | number: index and text: song name | rename 1 Metallica - One | rename song at index


Notes:
- Downloaded songs are added to current playlist, you need to reload playlist after download.
- Operations on playlists are saved to disk immediately.
