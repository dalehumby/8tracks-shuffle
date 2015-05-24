#!/usr/bin/env python
# encoding: utf-8
"""
8trackshuffle.py

The MIT License (MIT)

Copyright (c) 2014 Dale Humby

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
import logging
import requests
from time import sleep


class EighttracksError(Exception):
    pass

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

# Details of the user/bot that will log in and play the music to download
# Should not be the same as the user to follow
api_key = 'your_api_key'
user_name = 'username'
password = 'password'

# User that you want to follow and the collection of mixes to download
user_to_follow = '111111'
collection_to_follow = 'ipod-shuffle'

downloaded_mixes_file = 'downloadedmixes'
headers = {'X-Api-Key': api_key, 'X-Api-Version': 3}


def login():
    """Log in to 8tracks"""

    payload = 'login=%s&password=%s' % (user_name, password)
    r = requests.post('https://8tracks.com/sessions.json', data=payload, headers=headers)
    r = r.json()
    user_id = r['user']['id']
    logging.debug('%s, id %s', r['notices'], user_id)
    return user_id


def get_liked_mixes(user_id, collection='liked'):
    """
    Get the latest 12 mixes for a user
    Can be a collection such as 'liked' (when you click heart on web UI)
    or a collection name such as 'ipod'
    """

    if collection == 'liked':
        url = 'http://8tracks.com/mix_sets/liked:%s.json?include=mixes&per_page=500' % user_id
    else:
        url = 'http://8tracks.com/mix_sets/collection:%s:%s.json?include=mixes&per_page=500' % (user_id, collection)
    r = requests.get(url, headers=headers)
    if r.status_code >= 400:
        logging.error('Cannot find collection %s', collection)
        raise EighttracksError('Cannot find collection %s', collection)
    r = r.json()
    mixes = r['mix_set']['mixes']
    mix_list = []
    for mix in mixes:
        logging.debug('%s (%s)', mix['name'], mix['id'])
        mix_list.append(mix['id'])
    return mix_list


def find_mixes_to_download(liked_mixes):
    """Given a list of liked mixes, find the mixes that we havent already downloaded"""

    try:
        f = open(downloaded_mixes_file, 'r')
        downloaded_mixes = f.readlines()
    except IOError:
        downloaded_mixes = []  # if file doesnt exist

    downloaded_mixes = map(lambda downloaded_mixes: downloaded_mixes.strip(), downloaded_mixes)  # strip /n
    downloaded_mixes = map(int, downloaded_mixes)  # Change ['1234'] to [1234]
    mixes_to_download = []
    for liked_mix in liked_mixes:
        if liked_mix not in downloaded_mixes:
            mixes_to_download.append(liked_mix)
    return mixes_to_download


def add_mix_to_downloaded(mix_id):
    """
    Once all tracks in a mix have been downloaded add the mix to the list of all
    mixes that have already been downloaded
    """
    f = open(downloaded_mixes_file, 'a')
    f.write('%s\n' % mix_id)


def get_play_token():
    """
    Look for a play token in cached file, and if it's not there
    get it from 8tracks. Must be logged in first.
    """
    cache_file = 'playtoken'
    try:
        f = open(cache_file, 'r')
        play_token = f.readline()
        if play_token:
            return play_token
    except IOError:
        pass  # if file not found skip because next action is to create the file
    f = open(cache_file, 'w')
    r = requests.get('http://8tracks.com/sets/new.json', headers=headers)
    r = r.json()
    play_token = r['play_token']
    f.write(play_token)
    f.close()
    return play_token


def get_mix_details(mix_id):
    """Take a mix id and make a fodler from the mix name"""

    url = 'http://8tracks.com/mixes/%s.json' % mix_id
    r = requests.get(url, headers=headers)
    r = r.json()
    mix_name = clean_name(r['mix']['name'])
    tracks_count = r['mix']['tracks_count']
    return mix_name, tracks_count


def get_track(play_token, mix, method='play'):
    """
    Get a track of a mix
    method can be 'play' to start the session or 'next' to get the next track
    or 'skip' to skip to the next track
    """

    url = 'http://8tracks.com/sets/%s/%s.json?mix_id=%s' % (play_token, method, mix)
    r = requests.get(url, headers=headers)
    r = r.json()
    logging.debug(r)
    return r['set']


def find_extension(url):
    """Find the track filename extension within a URL"""

    from urlparse import urlparse
    from os.path import splitext, basename

    disassembled = urlparse(url)
    filename, file_ext = splitext(basename(disassembled.path))
    return file_ext[1:]


def download_track(track_set):
    """
    Given the track details, download the file and store locally
    """

    track = track_set['track']
    # if track['stream_source'] == 'upload_v3':
    url = track['track_file_stream_url']
    r = requests.get(url, headers=headers)
    if r.status_code >= 400:
        logging.error('Cannot get track, server returned %s', r.status_code)
        raise EighttracksError('Cannot download track')
    extension = find_extension(r.url)
    file_name = '%s - %s (%s).%s' % (track['name'], track['performer'], track['release_name'], extension)
    file_name = clean_name(file_name)
    f = open(file_name, 'wb')
    f.write(r.content)
    f.close()
    return file_name, extension


def get_play_length(file_name, file_format):
    """Find the length of the track in seconds"""

    from mutagen.mp3 import MP3
    from mutagen.m4a import M4A

    if file_format == 'mp3':
        audio = MP3(file_name)
    elif file_format == 'm4a':
        audio = M4A(file_name)
    else:
        raise Exception('Cannot get play length for format %s', file_format)
    play_length = audio.info.length
    logging.debug('Play length %s', play_length)
    return play_length


def report_track_as_played(play_token, mix_id, track_set):
    """
    8tracks requires you to report a track as
    played after 30s of listening
    """

    track_id = track_set['track']['id']
    url = 'http://8tracks.com/sets/%s/report.json?track_id=%s&mix_id=%s' % (play_token, track_id, mix_id)
    try:
        r = requests.get(url, headers=headers, timeout=10)
    except Timeout:
        pass


def write_playlist(mix_name, file_name, file_format, play_length):
    """
    Make an m3u playslist so when importing to iTunes the tracks are played
    in same order as on 8tracks.
    """

    playlist = '%s.m3u' % mix_name
    try:
        f = open(playlist, 'r')
    except IOError:
        f = open(playlist, 'w')
        f.write('#EXTM3U\n')
        f.close()
    f = open(playlist, 'a')
    f.write('#EXTINF:%s,%s\n' % (int(play_length), file_name[:-4]))
    f.write('%s\n' % file_name)
    f.close()


def clean_name(name):
    """
    Change Unicode to ASCII and remove unhelpful or illegal characters
    """
    name = name.encode('ascii', 'ignore')
    return name.translate(None, """#%&@${}|\/?'";:,<>*$+=!""")


def main():
    login()
    play_token = get_play_token()
    liked_mixes = get_liked_mixes(user_to_follow, collection_to_follow)
    mixes_to_download = find_mixes_to_download(liked_mixes)
    for mix_id in mixes_to_download:
        mix_name, tracks_count = get_mix_details(mix_id)
        try:
            os.mkdir(mix_name)
        except OSError:
            pass  # ignore if already exists
        os.chdir(mix_name)

        # download each track as if you were playing it
        logging.info('Playing %s: %s tracks', mix_name, tracks_count)
        track_set = get_track(play_token, mix_id, method='play')
        while not track_set['at_end']:
            try:
                file_name, file_format = download_track(track_set)
            except EighttracksError:
                track_set = get_track(play_token, mix_id, method='skip')
                continue
            play_length = get_play_length(file_name, file_format)
            write_playlist(mix_name, file_name, file_format, play_length)
            logging.info('Playing %s for %ss', file_name, play_length)
            logging.debug('Waiting 30s...')
            sleep(30)
            report_track_as_played(play_token, mix_id, track_set)
            sleep_time = (play_length - 30) / 2  # play at double speed...
            logging.debug('Waiting %ss...', sleep_time)
            sleep(sleep_time)
            track_set = get_track(play_token, mix_id, method='next')

        os.chdir('..')  # once all tracks in mix played go back up one directory level
        add_mix_to_downloaded(mix_id)

if __name__ == '__main__':
    main()
