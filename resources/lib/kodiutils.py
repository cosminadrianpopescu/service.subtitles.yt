# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
import xbmcgui
import sys
import re
import logging
import json as json
import logger


# read settings
ADDON = xbmcaddon.Addon()

def notification(header, message, time=5000, icon=ADDON.getAddonInfo('icon'), sound=True):
    xbmcgui.Dialog().notification(header, message, icon, time, sound)


def show_settings():
    ADDON.openSettings()


def get_setting(setting):
    return ADDON.getSetting(setting).strip().decode('utf-8')


def set_setting(setting, value):
    ADDON.setSetting(setting, str(value))


def get_setting_as_bool(setting):
    return get_setting(setting).lower() == "true"


def get_setting_as_float(setting):
    try:
        return float(get_setting(setting))
    except ValueError:
        return 0


def get_setting_as_int(setting):
    try:
        return int(get_setting_as_float(setting))
    except ValueError:
        return 0


def get_string(string_id):
    return ADDON.getLocalizedString(string_id).encode('utf-8', 'ignore')

def build_url(url):
    id = sys.argv[0]
    if (re.match("^/", url)):
        id = "plugin://%s" % ADDON.getAddonInfo("id")
        url = re.sub("^/", "", url)
    return "%s/%s" % (id, url)

def urlencode(url):
    return url.replace("/", "%2F")


def kodi_json_request(params):
    data = json.dumps(params)
    request = xbmc.executeJSONRPC(data)

    try:
        response = json.loads(request)
    except UnicodeDecodeError:
        response = json.loads(request.decode('utf-8', 'ignore'))

    try:
        if 'result' in response:
            return response['result']
        return None
    except KeyError:
        logger.log_warning("[%s] %s" %
                    (params['method'], response['error']['message']))
        return None
