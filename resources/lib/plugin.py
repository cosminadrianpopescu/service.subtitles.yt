# -*- coding: utf-8 -*-

import sys
import re
import os
import stat
import xbmc
import urllib
import json
import xbmcaddon
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory
from resources.lib import logger


ADDON = xbmcaddon.Addon()
__scriptid__   = ADDON.getAddonInfo('id')

# Main page

def get_params(string=""):
    param=[]
    if string == "":
        paramstring=sys.argv[2]
    else:
        paramstring=string
    if len(paramstring)>=2:
        params=paramstring
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param

def local_youtube_dl(id):
    addon = xbmcaddon.Addon()
    if (sys.platform == 'win32'):
        path = "%s/resources/bin/youtube-dl.exe" % str(addon.getAddonInfo("path"))
    else:
        path = "%s/resources/bin/youtube-dl" % str(addon.getAddonInfo("path"))
        if not os.access(path, os.X_OK):
            os.chmod(path, 0755)

    (stdin, stdout) = os.popen2("%s --write-auto-sub --simulate --dump-json -- %s" % (path, id))
    output = stdout.read()
    return json.loads(output)

def retrieve_search():
    path = xbmc.translatePath("special://temp")
    with open("%s/yt-subtitles-search" % path, 'r') as file:
        data = json.load(file)
        return data

def get_subtitles(json, key, type):
    subtitles = []
    for k in json[key]:
        s = json[key][k]
        if (isinstance(s, list)):
            vtts = filter(lambda x: x['ext'] == 'vtt', s)
            if (len(vtts) == 0):
                continue
            s = vtts[0]
        if s['ext'] != 'vtt':
            continue

        subtitles.append({'url': s['url'], 'lang': k, 'type': type})

    return subtitles

def get_id():
    url = xbmc.getInfoLabel("Player.Filenameandpath")
    return re.sub("^.*[=/]([^=/]+)$", r'\g<1>', url)

def search(params):
    langs = []
    for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
        if lang == "Portuguese (Brazil)":
            code = "pob"
        elif lang == "Greek":
            code = "ell"
        else:
            code = xbmc.convertLanguage(lang,xbmc.ISO_639_1)
        langs.append({'label': lang, 'code': code})

    logger.log("LANGUAGES ARE %s" % langs)
    id = get_id()
    logger.log("ID IS %s" % str(id))
    js = local_youtube_dl(id)
    subtitles = get_subtitles(js, 'requested_subtitles', 'Requested subtitle')
    subtitles = subtitles + get_subtitles(js, 'automatic_captions', 'Automatic subtitle')
    subtitles = subtitles + get_subtitles(js, 'subtitles', 'Subtitle')
    subtitles = filter(lambda x: x['lang'] in map(lambda x: x['code'], langs), subtitles)
    path = xbmc.translatePath("special://temp")
    with open("%s/yt-subtitles-search" % path, 'w') as file:
        json.dump(subtitles, file, indent=4)
    for s in subtitles:
        lang = filter(lambda x: x['code'] == s['lang'], langs)[0]
        listitem = ListItem(label = lang['label'], label2 = s['type'], thumbnailImage = s['lang'])
        url = "plugin://%s/?action=download&lang=%s&which=%s" % (__scriptid__, s['lang'], s['type'])
        addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

    endOfDirectory(int(sys.argv[1]))

def download(params):
    logger.log("DOWNLOAD PARAMS ARE %s" % str(params))
    json = retrieve_search()
    path = xbmc.translatePath("special://temp")
    search = retrieve_search()
    sub = filter(lambda x: x['lang'] == params['lang'] and x['type'] == params['which'], search)
    if (len(sub) == 0):
        raise ValueError('SUBTITLE NOT FOUND %s WITH PARAMS %s' % (str(sub), str(params)))
    f = urllib.urlopen(sub[0]['url'])
    result = "%ssub.srt" % path
    with open(result, "wb") as file:
        file.write(f.read())
    file.close()
    xbmc.sleep(500)

    listitem = ListItem(label=result)
    addDirectoryItem(handle=int(sys.argv[1]),url=result,listitem=listitem,isFolder=False)
    endOfDirectory(int(sys.argv[1]))

def run():
    params = get_params()
    logger.log("PARAMS ARE %s" % str(params))
    if (params['action'] == 'search'):
        search(params)
        return

    if (params['action'] == 'download'):
        download(params)
        return
