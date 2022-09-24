# Album Poster Creater
# Made by Elliot Jarnit

version = "1.0.0"

# TODO
# - Make long album names print on 2 lines
# - Copyright info on bottom
# - Tracklist with track length

import urllib.parse
import requests
import json
import inquirer
from PIL import Image, ImageDraw, ImageFont
import urllib.request
from yaspin import yaspin
import warnings
import os
import sys

warnings.filterwarnings("ignore", category=DeprecationWarning)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def clearConsole():
    print('\n' * 100)


def get_colors(img):
    paletted = img.convert('P', palette=Image.ADAPTIVE, colors=5)
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)
    colors = list()
    for i in range(5):
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


print("Album poster creator by Elliot Jarnit")
print("Version " + version)
search = input("Enter the album name\n> ")

# Search for albums
url = 'https://itunes.apple.com/search?term=' + urllib.parse.quote(
    search) + '&entity=album&limit=10'
response = requests.get(url)
res_json = json.loads(response.text)
clearConsole()

# Make neat list of album choices
choices = []
if int(res_json['resultCount']) == 0:
    print("No results found...")
    exit()
for i in res_json['results']:
    choices.append(i['collectionName'] + ' by ' + i['artistName'])

# Ask user to select album
questions = [
    inquirer.List('album', message="Choose an album", choices=choices),
    inquirer.List(
        'smallfont',
        message=
        "Do you want to use a smaller font for the track list? (select yes if songs go off screen)",
        choices=["No", "Yes"])
]
prompt_answer = inquirer.prompt(questions)
clearConsole()

# Get the specific album
album = res_json['results'][choices.index(prompt_answer['album'])]

# Get the track list and track times
# This will create a list with 5 tracks, then those 5 tracks times (in order) and so on.
# Someone else try to find a better way to do this because this was all I could think of
url = 'https://itunes.apple.com/lookup?id=' + str(
    album['collectionId']) + '&entity=song'
response = requests.get(url)
response = json.loads(response.text)
tracklist = []
cur = 1
savedup = []
linesoftracks = 5
if prompt_answer["smallfont"] == "Yes":
    smallerfont = True
else:
    smallerfont = False
if album["trackCount"] > 15:
    linesoftracks = 6
if album["trackCount"] > 20:
    linesoftracks = 7
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

# Get important details
album_artwork_link = album['artworkUrl100'].replace('100x100bb.jpg',
                                                    '600x600bb.jpg')
album_name = album["collectionName"]
album_year = album['releaseDate'].split('-')[0]
album_artist = album['artistName']
album_copyright = album['copyright'].replace("℗", "(c)")

# Warn user if album name is too long
if len(album_name) > 30:
    questions = [
        inquirer.List(
            'newname',
            message=
            "Album name is too long. This might cause the poster to look bad. Do you want to edit the album name?",
            choices=["Yes", "No"],
        )
    ]
    prompt_answer = inquirer.prompt(questions)
    clearConsole()
    if (prompt_answer["newname"] == "Yes"):
        album_name = input("Album name to put on poster\n> ")
        clearConsole()

# Start the loading spinner
spinner = yaspin(text="Generating Poster")
spinner.start()
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
while length > 480:
    font_name = ImageFont.truetype(resource_path('fonts/album_name.ttf'), cursize)
    font_year = ImageFont.truetype(resource_path('fonts/album_year.ttf'), int(cursize / 2) + 5)
    length = font_name.getlength(album_name) + font_year.getlength(
        album_year) + 77
    cursize -= 1
# Load static fonts
font_artist = ImageFont.truetype(resource_path('fonts/album_name.ttf'), 25)
font_tracks = ImageFont.truetype(resource_path('fonts/album_tracks.ttf'), 15)
font_times = ImageFont.truetype(resource_path('fonts/album_tracks.ttf'), 15)
font_copyright = ImageFont.truetype(resource_path('fonts/album_tracks.ttf'), 10)
# Check if font needed to be smaller
if smallerfont:
    font_tracks = ImageFont.truetype(resource_path('fonts/album_tracks.ttf'), 14)
    font_times = ImageFont.truetype(resource_path('fonts/album_tracks.ttf'), 14)
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
        if smallerfont:
            cury -= 5
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
    curx += 30
    if smallerfont:
        curx -= 10
# Add copyright info in corner
posterdraw.text((720 / 2, 960),
                album_copyright,
                font=font_copyright,
                fill=(0, 0, 0),
                anchor='md')
# Delete album artwork
os.remove('albumartwork.jpg')
# Save the image
poster.save(album_name.replace(" ", "") + ".png")
# Stop the spinner
spinner.ok("✅ ")
