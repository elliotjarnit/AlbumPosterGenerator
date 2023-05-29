import urllib.parse
import json
from PIL import Image, ImageDraw, ImageFont
import os
import sys
from io import BytesIO
import warnings
import requests
import pyodide_http

pyodide_http.patch_all()

warnings.filterwarnings("ignore", category=DeprecationWarning)

fonts = {
    "thin": requests.get("https://files.elliotjarnit.dev/fonts/thin.otf"),
    "verylight": requests.get("https://files.elliotjarnit.dev/fonts/verylight.otf"),
    "light": requests.get("https://files.elliotjarnit.dev/fonts/light.otf"),
    "regular": requests.get("https://files.elliotjarnit.dev/fonts/regular.otf"),
    "medium": requests.get("https://files.elliotjarnit.dev/fonts/medium.otf"),
    "semibold": requests.get("https://files.elliotjarnit.dev/fonts/semibold.otf"),
    "bold": requests.get("https://files.elliotjarnit.dev/fonts/bold.otf"),
    "verybold": requests.get("https://files.elliotjarnit.dev/fonts/verybold.otf"),
}

def find_line_split(text):
    middle = len(text) // 2
    before = text.rfind(' ', 0, middle)
    after = text.find(' ', middle + 1)
    if before == -1 or (after != -1 and middle - before >= after - middle):
        middle = after
    else:
        middle = before
    return middle

def get_colors(img):
    try:
        paletted = img.convert('P', palette=Image.ADAPTIVE, colors=5)
        palette = paletted.getpalette()
        color_counts = sorted(paletted.getcolors(), reverse=True)
        colors = list()
        for i in range(5):
            palette_index = color_counts[i][1]
            dominant_color = palette[palette_index * 3:palette_index * 3 + 3]
            colors.append(tuple(dominant_color))
    except:
        paletted = img.convert('P', palette=Image.ADAPTIVE, colors=1)
        palette = paletted.getpalette()
        color_counts = sorted(paletted.getcolors(), reverse=True)
        colors = list()
        for i in range(1):
            palette_index = color_counts[i][1]
            dominant_color = palette[palette_index * 3:palette_index * 3 + 3]
            colors.append(tuple(dominant_color))
    return colors


def remove_featured(str):
    if (str.find("(") != -1):
        str = str.split("(")[0].strip()
    return str


def format_time(millis):
    minutes = str(int((millis / (1000 * 60)) % 60))
    seconds = str(int((millis / 1000) % 60))

    if len(seconds) == 1:
        seconds = "0" + seconds

    return minutes + ":" + seconds

def create_track_list(linesoftracks, response):
    # Get the track list and track times
    # This will create a list with 5 tracks, then those 5 tracks times (in order) and so on.
    # Someone else try to find a better way to do this because this was all I could think of
    tracklist = []
    cur = 1
    savedup = []
    for i in response["results"]:
        if (i["wrapperType"] == "track"):
            if cur > linesoftracks:
                cur = 1
                for x in savedup:
                    tracklist.append(x)
                savedup = []
            tracklist.append(remove_featured(i["trackName"]))
            savedup.append(format_time(i["trackTimeMillis"]))
            cur += 1
    if len(savedup) > 0:
        tracklist.append("-")
        for x in savedup:
            tracklist.append(x)
    return tracklist

def generatePoster(data):
    album = data["results"][0]

    # Get important details
    album_artwork_link = album['artworkUrl100'].replace('100x100bb.jpg',
                                                        '600x600bb.jpg')
    album_name = album["collectionName"]
    album_year = album['releaseDate'].split('-')[0]
    album_artist = album['artistName']
    album_copyright = album['copyright'].replace("℗", "(c)")

    if len(sys.argv) > 0:
        if ("--nocopyright" in sys.argv):
            album_copyright = ""

    # Download artwork
    urllib.request.urlretrieve(album_artwork_link, 'albumartwork.jpg')
    # Open the artwork
    albumart = Image.open('albumartwork.jpg')
    # Create a new blank image
    poster = Image.new("RGB", (720, 960), color=(255, 255, 255))
    # Put artwork on blank image
    poster.paste(albumart, (60, 60))
    posterdraw = ImageDraw.Draw(poster)
    # Draw seperator
    posterdraw.rectangle([60, 740, 660, 745], fill=(0, 0, 0))
    # Calculate font size for large album names
    length = 1000
    cursize = 55
    twolinesforalbum = False
    while length > 480 and cursize >= 25:
        font_name = ImageFont.truetype(BytesIO(fonts["verybold"].content), cursize)
        font_year = ImageFont.truetype(BytesIO(fonts["medium"].content), int(cursize / 2) + 5)
        length = font_name.getlength(album_name) + font_year.getlength(
            album_year) + 77
        cursize -= 1

    if cursize < 25 and length > 480:
        twolinesforalbum = True
        length = 1000
        cursize = 55

        temp = []
        temp.append(album_name[:find_line_split(album_name)].strip())
        temp.append(album_name[find_line_split(album_name):].strip())
        album_name = temp

        albumnametocompare = ""
        if len(album_name[0]) > len(album_name[1]):
            albumnametocompare = album_name[0]
        else:
            albumnametocompare = album_name[1]


        while length > 480 or cursize >= 25:
            font_name = ImageFont.truetype(BytesIO(fonts["verybold"].content), cursize)
            font_year = ImageFont.truetype(BytesIO(fonts["medium"].content), int(cursize / 2) + 5)

            length = font_name.getlength(albumnametocompare) + font_year.getlength(
                album_year) + 77
            cursize -= 1

    print(cursize)
    print(length)
    print(albumnametocompare)
    # Load static fonts
    font_artist = ImageFont.truetype(BytesIO(fonts["semibold"].content), 25)
    font_copyright = ImageFont.truetype(BytesIO(fonts["light"].content), 10)

    # Get first tracklist
    linesoftracks = 5
    tracklist = create_track_list(linesoftracks, data)

    # Extremely complicated font size calculation
    # This is to make sure the tracklist fits on the poster with the biggest font size possible
    # If you want to try and figure out how this works, good luck
    bestsize = 0
    besttracks = []
    bestlinesoftracks = 0

    while True:
        length = 1000
        cursize = 17
        while length > 600:
            cursize -= 1
            font_tracks = ImageFont.truetype(BytesIO(fonts["regular"].content), cursize)
            font_times = ImageFont.truetype(BytesIO(fonts["regular"].content), cursize)
            length = 0
            max = 0
            for j in range(0, len(tracklist) - 1, linesoftracks * 2):
                for i in range(j, j + linesoftracks):
                    try:
                        if max < font_tracks.getlength(tracklist[i]):
                            max = font_tracks.getlength(tracklist[i])
                    except:
                        break
                length += max + font_times.getlength("00:00") + 30
        if cursize > bestsize:
            bestsize = cursize
            besttracks = tracklist
            bestlinesoftracks = linesoftracks
        linesoftracks += 1
        tracklist = create_track_list(linesoftracks, data)
        if linesoftracks > 9:
            break

    # Load best font
    font_tracks = ImageFont.truetype(BytesIO(fonts["regular"].content), bestsize)
    font_times = ImageFont.truetype(BytesIO(fonts["regular"].content), bestsize)
    tracklist = besttracks
    linesoftracks = bestlinesoftracks


    # Put album name on image
    posterdraw.text((65, 725),
                    album_name,
                    font=font_name,
                    fill=(0, 0, 0),
                    anchor='ls')
    # Calculate where the year goes on image
    albumnamebbox = posterdraw.textbbox((20, 20), "a", font=font_name)
    albumyearbbox = posterdraw.textbbox((20, 20), "a", font=font_year)
    # Put the year on image
    posterdraw.text((77 + font_name.getlength(album_name), 725),
                    album_year,
                    font=font_year,
                    fill=(0, 0, 0),
                    anchor='ls')
    # Get dominant colors
    domcolors = get_colors(albumart)
    # Put dominant color rectangles on poster
    x = 660
    rectanglesize = 30
    for i in domcolors:
        posterdraw.rectangle([(x - rectanglesize, 670), (x, 670 + rectanglesize)],
                            fill=(i))
        x -= rectanglesize
    # Put album artist on poster
    posterdraw.text((660, 725),
                    album_artist,
                    font=font_artist,
                    fill=(0, 0, 0),
                    anchor='rs')
    # Put the tracks onto the poster
    curline = 1
    curx = 775
    cury = 60
    maxlen = 0
    track = True

    for cur in tracklist:
        if curline > linesoftracks or cur == "-":
            if track:
                cury += maxlen + 46
            else:
                cury += maxlen + 15
            curx = 775
            curline = 1
            maxlen = 0
            track = not track
            if cur == "-":
                continue
        if font_tracks.getlength(cur) > maxlen:
            maxlen = font_tracks.getlength(cur)
        if track:
            posterdraw.text((cury, curx),
                            cur,
                            font=font_tracks,
                            fill=(0, 0, 0),
                            anchor='ls')
        else:
            posterdraw.text((cury, curx),
                            cur,
                            font=font_times,
                            fill=(0, 0, 0),
                            anchor='rs')
        curline += 1
        curx += (int(cursize / 2) + 5) * 2


    return poster