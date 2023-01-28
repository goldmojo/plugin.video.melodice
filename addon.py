import xbmc
import xbmcaddon
import xbmcgui

import http.client
import urllib.parse

import re
import sys

addonID = 'plugin.video.melodice'
addon = xbmcaddon.Addon (addonID)
addonname = addon.getAddonInfo ('name')
 
boardgamename = xbmcgui.Dialog().input ("Game name", type=xbmcgui.INPUT_ALPHANUM)

# Open Melodice connection
https_url = 'melodice.org'
httpcon = http.client.HTTPSConnection (https_url)
# http.client debug level => Set to 1 to debug
httpcon.set_debuglevel (0)

# Get CSRF token
httpcon.request("GET", "/")
response = httpcon.getresponse()
webpage = response.read().decode('utf-8')
CSRF_re = re.compile (r'^.*name=\'csrfmiddlewaretoken\'\s+value=\'(?P<CSRF>\S+)\'.*$')
CSRF_token = None
for line in webpage.split('\n'):
    m = CSRF_re.match (line)
    if m:
        if CSRF_token:
            if m.group ('CSRF') != CSRF_token:
                xbmc.log ("Melodice : 2 different CSRF tokens parsed", xbmc.LOGWARNING)
        else:
            CSRF_token = m.group ('CSRF')
if not CSRF_token:
    xbmc.log ("Melodice : CSRF token missing", xbmc.LOGERROR)
    sys.exit (1)

# Melodice search API call
params = urllib.parse.urlencode({'csrfmiddlewaretoken': CSRF_token, 'q': boardgamename})

headers = {
    'Cookie' : 'csrftoken=' + CSRF_token,
    'User-Agent' : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30",
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://' + https_url}

httpcon.request('POST', '/', params, headers)
response = httpcon.getresponse()

playlist_webpage = None
if response.status == 302:
    if response.getheader('Location'):
        playlist_webpage = response.getheader('Location')
        response.read().decode('utf-8')
    else:
        xbmcgui.Dialog().ok ('Melodice', 'Game playlist not found, exiting ...')
        xbmc.log ("Melodice : Game playlist not found", xbmc.LOGERROR)
        sys.exit (1)
else:
    xbmcgui.Dialog().ok ('Melodice', 'Game playlist not found, exiting ...')
    xbmc.log ("Melodice : Game playlist not found", xbmc.LOGERROR)
    sys.exit (1)

# Get the playlist from Melodice search result webpage
httpcon.request("GET", playlist_webpage)
response = httpcon.getresponse()
webpage = response.read().decode('utf-8')
playlist_re = re.compile (r'^.*http://www.youtube.com/watch_videos%3Fvideo_ids=(?P<TAGS>\S+?)".*$')
youtube_tags = []
for line in webpage.split('\n'):
    m = playlist_re.match (line)
    if m:
        youtube_tags = m.group ('TAGS').split(',')

# Close Melodice connection
httpcon.close()

# Game found, but no playlist yet
if len(youtube_tags) == 0:
    xbmcgui.Dialog().ok ('Melodice', 'Game found but no playlist yet, exiting ...')
    xbmc.log ("Melodice : Game found but no playlist yet", xbmc.LOGERROR)
    sys.exit (0)

# Create kodi playlist
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
playlist.clear()

index = 1

for tag in youtube_tags:
    # Path to let videos be played by the youtube plugin
    youtubePath = 'plugin://plugin.video.youtube/play/?video_id='
    # Add youtube tag to path to make videos play with the kodi youtube plugin
    path = youtubePath + tag
    # Create listitem to insert in the playlist
    list_item = xbmcgui.ListItem (label=str(index))
    list_item.setProperty ('IsPlayable', 'true')
    # Add list_item to the playlist
    playlist.add (path, list_item, index)
    # increment the playlist index
    index = index + 1

# Play the playlist
xbmc.Player().play (playlist, windowed=False)