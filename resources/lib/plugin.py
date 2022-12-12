# -*- coding: utf-8 -*-

import sys
import re
import os
import subprocess
import stat
import xbmc
import urllib
import json
import xbmcaddon
from urllib.parse import unquote
from urllib.request import urlopen
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
        path = "%s/resources/bin/yt-dlp" % str(addon.getAddonInfo("path"))
        if not os.access(path, os.X_OK):
            os.chmod(path, stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    process = subprocess.run([path, "--write-auto-sub", "--simulate", "--dump-json", "--", id], capture_output=True)
    return json.loads(process.stdout)

def retrieve_search():
    path = xbmc.translatePath("special://temp")
    with open("%s/yt-subtitles-search" % path, 'r') as file:
        data = json.load(file)
        return data

def get_subtitles(json, key, type):
    subtitles = []
    if not key in json or json[key] == None:
        return subtitles
    for k in json[key]:
        s = json[key][k]
        if (isinstance(s, list)):
            vtts = list(filter(lambda x: x['ext'] == 'vtt', s))
            if len(vtts) == 0:
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
    for lang in unquote(params['languages']).split(","):
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
    subtitles = list(filter(lambda x: x['lang'] in map(lambda x: x['code'], langs), subtitles))
    path = xbmc.translatePath("special://temp")
    with open("%s/yt-subtitles-search" % path, 'w') as file:
        json.dump(subtitles, file, indent=4)
    for s in subtitles:
        lang = list(filter(lambda x: x['code'] == s['lang'], langs))[0]
        listitem = ListItem(label = lang['label'], label2 = s['type'])
        listitem.setArt({'thumb': s['lang']})
        url = "plugin://%s/?action=download&lang=%s&which=%s" % (__scriptid__, s['lang'], s['type'])
        addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

    endOfDirectory(int(sys.argv[1]))

def _prepare_sub_txt(sub):
    xbmc.log("PREPARING %s" % sub.replace("\n", ""), xbmc.LOGINFO)
    p1 = r"<[0-9]{2}:[0-9]{2}"
    if re.search(p1, sub, re.M) == None:
        xbmc.log("RETURNING UNMODIFIED STRING", xbmc.LOGINFO)
        return sub

    lines = sub.split("\n")
    result = ""
    p2 = "^[0-9:\\.]+[ ]+-->[ ]+[0-9:\\.]+.*$"
    started_timings = False
    for line in lines:
        if not started_timings and re.search(p2, line) == None:
            result += line + "\n"
            continue
        if re.search(p2, line) != None or line == "" or re.search(p1, line) != None:
            result += line + "\n"
            started_timings = True
            continue

    return result

def download(params):
    logger.log("DOWNLOAD PARAMS ARE %s" % str(params))
    json = retrieve_search()
    path = xbmc.translatePath("special://temp")
    search = retrieve_search()
    sub = list(filter(lambda x: x['lang'] == params['lang'] and x['type'] == params['which'], search))
    if (len(sub) == 0):
        raise ValueError('SUBTITLE NOT FOUND %s WITH PARAMS %s' % (str(sub), str(params)))
    f = urlopen(sub[0]['url'])
    result = "%ssub.srt" % path
    with open(result, "wb") as file:
        x = f.read()
        txt = _prepare_sub_txt(x.decode())
        file.write(txt.encode('utf-8'))
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
