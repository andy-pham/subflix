#! coding: utf-8

import re
import os
import sys
import time
import pprint
import urllib
import urllib2
import pyquery
import zipfile
import cStringIO
import simplejson
import subprocess


def get_movie_title(imdb_id):
    r = urllib2.urlopen('http://www.omdbapi.com/?i=' + imdb_id)
    return simplejson.loads(r.read()).get('Title')


def search_google(query):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent',
                          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                          '35.0.1916.114 Safari/537.36'),
                         ('Accept-Language', 'en-US,en;q=0.8,vi;q=0.6')]
    r = opener.open('https://www.google.com.vn/search?q='
                    + urllib.quote_plus(query))
    return r.read()


def get_imdb_id(torrent_name):
    html = search_google(torrent_name + ' imdb')
    imdb_ids = re.findall('/title/(tt\d+)/',
                          html.replace('\n', ''), re.MULTILINE)
    return imdb_ids[0]


def get_subscene_url(imdb_id):
    html = search_google('%s site:subscene.com' % imdb_id)
    urls = [pyquery.PyQuery(i).text() for i in pyquery.PyQuery(html)('cite')]
    url = [i for i in urls if '/subtitles/' in i][0]
    return 'http://' + re.findall('(subscene.com/subtitles/.*?/)', url)[0]


def get_similarity_score(subtitle_name, torrent_name):
    normalize_subtitle_name = ''.join([c if c.isalnum() else ' '
                                       for c in subtitle_name]).lower()
    normalize_torrent_name = ''.join([c if c.isalnum() else ' '
                                      for c in torrent_name]).lower()
    subtitle_words = normalize_subtitle_name.split()
    torrent_words = normalize_torrent_name.split()
    matches = []
    for word in subtitle_words:
        if word in torrent_words:
            matches.append(word)
    return len(matches)


def get_subtitles(movie_filename, language):
    imdb_id = get_imdb_id(movie_filename)
    if not imdb_id:
        return False

    try:
        url = get_subscene_url(imdb_id)
        print url
        r = urllib2.urlopen(url)
    except urllib2.HTTPError:
        return False

    doc = pyquery.PyQuery(r.read())
    subs = doc('.content table tbody tr a')

    subtitles = []
    for sub in subs:
        sub = doc(sub)
        subtitle_url = sub.attr('href')
        if subtitle_url.startswith('/'):
            subtitle_url = 'http://subscene.com' + subtitle_url
        subtitle_lang = sub('span.l').text().lower()
        subtitle_name = sub('span:not(.l)').text()
        subtitles.append({'lang': subtitle_lang,
                          'name': subtitle_name,
                          'url': subtitle_url,
                          'score': get_similarity_score(subtitle_name,
                                                        movie_filename)})
    subtitles = [s for s in subtitles if s['lang'] == language]
    subtitles.sort(key=lambda k: k['score'], reverse=True)
    subtitles = subtitles[:5]

    for subtitle in subtitles:
        if subtitle.get('lang') != language.lower():
            continue

        r = urllib2.urlopen(subtitle.get('url'))
        doc = pyquery.PyQuery(r.read())

        # Score
        #
        # weight:
        #   - rating: 0.3
        #   - rating count: 0.2
        #   - name match score: 0.5

        rating = doc('.header div.rating span').text()
        if rating and rating[0].isdigit():
            rating = int(rating[0]) * 0.5
        else:
            rating = -1 * 0.3

        rating_count = [i for i in
                        doc('.header div.rating').attr('data-hint').split()
                        if i.isdigit()]
        if rating_count and rating_count[0].isdigit():
            rating_count = int(rating_count[0])
            rating += rating_count * 0.2

        subtitle['score'] = rating + subtitle.get('score') * 0.5

        # Extract subtitle download url
        download_url = doc(doc('.header .download a')[0]).attr('href')
        if download_url.startswith('/'):
            download_url = 'http://subscene.com' + download_url

        subtitle['download_url'] = download_url

    subtitles.sort(key=lambda k: k['score'], reverse=True)
    return subtitles


def get_subtitle_file(download_url):
    data = urllib2.urlopen(download_url).read()
    z = zipfile.ZipFile(cStringIO.StringIO(data))
    srt_files = [i.filename for i in z.filelist
                 if i.filename.rsplit('.')[-1].lower() in ['srt', 'ass']]
    return z.extract(srt_files[0], '/tmp/')


if __name__ == '__main__':
    language = sys.argv[1]
    movie_link = sys.argv[2]

    # Magnet link
    if movie_link.startswith('magnet:'):
        magnet_link = movie_link
        movie_filename = urllib.unquote_plus(magnet_link)\
                               .split('&dn=')[-1]\
                               .split('&')[0]

    # Torrent file & HTTP direct link
    elif movie_link.startswith('http://') or movie_link.startswith('https://'):
        movie_filename = movie_link.rsplit('/', 1)[-1].rsplit('.', 1)[0]

    # Others
    else:
        raise NotImplementedError()

    subtitles = get_subtitles(movie_filename, language)
    if subtitles:
        pprint.pprint(subtitles[0])
        subtitle = get_subtitle_file(subtitles[0].get('download_url'))
    else:
        subtitle = None

    if movie_link.startswith('magnet:') or movie_link.endswith('.torrent'):
        command = ['peerflix', magnet_link,
                   '--vlc', '--remove', '--connections', '30']
        if subtitle:
            command.append('--subtitles')
            command.append(subtitle)
    else:
        command = ['/Applications/VLC.app/Contents/MacOS/VLC', movie_link]
        if subtitle:
            command.append('--sub-file')
            command.append(subtitle)

    p = subprocess.Popen(command)
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    p.kill()
    if subtitle:
        os.unlink(subtitle)
    sys.exit()
