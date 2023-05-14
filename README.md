# Term-Music 

**still in development**

Terminal music player with audio visualization and youtube-dl integration.

![](https://github.com/tracksuitdev/term-music/blob/master/assets/term-music.gif?raw=true)

## Installation

Clone the repo and change `DOWNLOAD_FOLDER` in `config.py` to the folder where you want to store your music.

## Usage
Inside your download folder all .mp3 files will be considered as songs and all .txt files will be considered as 
playlists.

Playlist files should be text files with each line containing the name of a song (without extension) that is in your library.


```
usage: music [-h] [-v] {play,playall,playlist,ls,load} ...

positional arguments:
  {play,playall,playlist,ls,load}
    play                play a song
    playall             play all songs or playlists
    playlist            play playlist
    ls                  list songs
    load                download a list of songs

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
```

### play

```
usage: music play [-h] [-e] [-nd] query [query ...]

positional arguments:
  query              query used to search the library or youtube for the song
                     to play

options:
  -h, --help         show this help message and exit
  -e, --exact        only use exact matches to play a song from library, will
                     not search youtube or download a song
  -nd, --nodownload  don't search youtube and download the song if none is
                     found in library

```

### playall

```
usage: music playall [-h] [{songs,playlists}]

positional arguments:
  {songs,playlists}

options:
  -h, --help         show this help message and exit
```

### playlist

```
usage: music playlist [-h] [-e] query

positional arguments:
  query        query used to search the library for a playlist to play

options:
  -h, --help   show this help message and exit
  -e, --exact  only play a playlist if exact match is found
```

### ls

```
usage: music ls [-h] [-a] [-p] [-f]

options:
  -h, --help      show this help message and exit
  -a, --all       list all songs and playlists
  -p, --playlist  list only playlists
  -f, --full      list all songs with playlists they are on
```

### load

```
usage: music load [-h] [-p PLAYLIST] [-c] songs [songs ...]

positional arguments:
  songs                 list of songs to download in music library

options:
  -h, --help            show this help message and exit
  -p PLAYLIST, --playlist PLAYLIST
                        name of the playlist that will be made out of
                        downloaded songs
  -c, --check           if true will check if song already exists and won't
                        download it
```
