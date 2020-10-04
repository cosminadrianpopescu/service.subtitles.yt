# Kodi youtube subtitles

Small plugin to download subtitles for youtube videos based on the video ID.
It should work with the [official youtube
addon](https://github.com/jdf76/plugin.video.youtube) and any other addon
which exposes the video ID in the xbmc play url. 

Basically, if the video can be retrieved like this:

```
url = xbmc.getInfoLabel("Player.Filenameandpath")
return re.sub("^.*[=/]([^=/]+)$", r'\g<1>', url)
```

This should comprise most of the youtube kodi plugins.

# Note

If anybody has a problem with me using the official kodi addon fanart, please
let me know.

Enjoy!
