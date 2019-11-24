from pytube import YouTube, Playlist
from moviepy.editor import *
import mutagen
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from pydub import AudioSegment
import os
import sys
from utils.parsers import *
from utils.cmd_line import *

print("++++++++++++++++++++++++++++ Vbtesh's video converter - VVC ++++++++++++++++++++++++++++ \n")

# Validating inputs
print("""Enter below the track's URL or the name of the file for multiple extracts.

Playlist can only be extracted as single urls, not files.

If you are using a file, it should be a *.txt with one URL per line, see file in_template.txt located at ./inputs.
Forced metadata should follow the url on the same line, file pattern should be, if none is provided, leave unchanged:
{url;;album;;artist;;title;;year;;track_number;;genre} see /input/in_template.txt for full information.
File name format: in_*.txt and should be in 'inputs/'.""")
while True:
    payload = input("URL / File path: ")
    
    validation = []


    if payload[:8] == "https://":
        
        if "=PL" in payload:

            print("Track appears to be part of a playlist, do you want to download all of it?")
            check = input("\n [y]/[Enter]    [n] ==> ")

            if check == "n" or check == "no":
                try:
                    validation.append([YouTube(payload), payload, None])
                    print("Got it, proceeding with one video...\n")
                    break
                except:
                    print("Invalid url or couldn't connect to server, check connection and try again. If this message persist, check input.\n")
                    continue
            else:
                try:
                    validation.append([Playlist(payload), payload, None])
                    print("Got it, proceeding with one video...\n")
                    break
                except:
                    print("Invalid url or couldn't connect to server, check connection and try again. If this message persist, check input.\n")
                    continue
        else:
            try:
                validation.append([YouTube(payload), payload, None])
                print("Got it, proceeding with one video...\n")
                break
            except:
                print("Invalid url or couldn't connect to server, check connection and try again. If this message persist, check input.\n")
                continue
        
    elif payload[:3] == "in_":
        try:
            validation = read_urls(payload)
        except:
            print("Invalid file format or urls, check input file.\n")
            continue

        print("Trying to extract {number} videos? Yes [Enter] or [y], No [*] ".format(number = len(validation)))
        response = input("Response:")
        if response == "" or response == "y":
            print("Got it, proceeding...\n")
            break
        else:
            print("OK. Please check input file and reload.\n")
            continue
            
    else:
        print("Invalid input format, must be a YouTube url or a in_*.txt file in the /inputs/ folder.\n")
        continue

# Metadata validation
print("Constructing metadata for input tracks...\n")
download = []
for tune in validation:
    # Infos & album validation loop
    print("Handling {x}.".format(x=tune[0].title))
    print("URL: " + tune[1])
    while True:
        nature = input("Album or single track? album: [a]  single track: [t]/[Enter] ==> ")
        if nature == "a":
            album = True
            break
        elif nature == "t" or nature == "":
            album = False
            break
        else:
            continue
    
    if album:
        # if album, try parsing description for tracklist, if not found, look for file with data, if not found, ask to produce one
        print("Attempting to parse description for tracklist...\n")
        track_list = parse_tracklist(tune[0].description)
        if track_list:
            print("Track list found:")
            for track in track_list:
                print(track[0], "-", track[1], "-", track[2])
            check = input("\nValidate track list? [y]/[Enter]    [n] ==> ")
            if check == "n" or check == "no":
                track_list = None
            else:
                print("Track list validated.\n")
        if not track_list:
            print("Could not parse track list or invalid parsing result. Provide file name for track file.")
            print("Appropriate format is ts_*.txt, with the following format: {track_number;;timestamp (HH:MM:SS);;title}")
            print("The file has to be in the 'inputs' directory.")
            while True:
                file = input("File name: ")
                if file[-4:] == ".txt" and file[:3] == "ts_":
                    track_list = read_tracklist(file)
                    if track_list:
                        print("Track list found:")
                        for track in track_list:
                            print(track[0], "-", track[1], "-", track[2])
                        check = input("\nValidate track list? [y]/[Enter]    [n] ==> ")
                        if check != "" or check != "y":
                            print("Track list validated.\n")
                            break
                        else:
                            print("OK. Amend file and re submit.")
                    else:
                        print("No proper tracklist found. Check file and line format and re submit.")
                else:
                    print("Invalid file, check file name and re submit.")
        
        # Title
        print("Parsing title data...")
        metadata = parse_title(tune[0].title, True)
        print("Parsed metadata is as follows:")
        print_metadata(metadata)
        # Amendments
        change = input("Any amendments or additions? [y]    [n]/[Enter] ==> ")
        if change == "y":
            metadata = amend_metadata(metadata)
        # send to download list
        download.append([tune[0], tune[1], metadata, track_list])

    elif tune[2]:
        metadata = tune[2]

        parsed_metadata = parse_title(tune[0].title, False)

        if "title" not in metadata.keys():
            metadata["title"] = parsed_metadata["title"]
        if "artist" not in metadata.keys():
            metadata["artist"] = parsed_metadata["artist"]
        if "album" not in metadata.keys():
            metadata["album"] = parsed_metadata["album"]
        if "date" not in metadata.keys():
            metadata["date"] = parsed_metadata["date"]

        print("Parsed metadata is as follows:")
        print_metadata(metadata)
        # Amendments
        change = input("Any amendments or additions? [y]    [n]/[Enter] ==> ")
        if change == "y":
            metadata = amend_metadata(metadata)
        # send to download list
        download.append([tune[0], tune[1], metadata])
    
    else:
        # if track:
        # parse title, make amendments
        metadata = parse_title(tune[0].title, False)
        print("Parsed metadata is as follows:")
        print_metadata(metadata)
        # Amendments
        change = input("Any amendments or additions? [y]    [n]/[Enter] ==> ")
        if change == "y":
            metadata = amend_metadata(metadata)
        # send to download list
        download.append([tune[0], tune[1], metadata])

# Download, convert files and create mp3 final outputs
album_titles = []
for tube in download:
    if tube[2]["album"] not in album_titles:
        album_titles.append(tube[2]["album"])
if len(album_titles) > 1:
    track_list_album = False
else:
    track_list_album = True


final_info = []
track_number = 1
for tube in download:
    if len(tube) == 3 and track_list_album:
        title = tube[2]["title"]
        video_title = tube[0].title
        print("\nHandling one track:")
        print("Artist:", tube[2]["artist"])
        print("Title:", title)
        
        # Check if MP4 exists, if not download it
        tube_path = f".\\videos\\{video_title}.mp4"
        if not os.path.exists(tube_path):
            print("Downloading...")
            tube_path = tube[0].streams.first().download(output_path = ".\\videos\\")
            print("Download successful. Video file located at {}".format(tube_path))
        else:
            print("MP4 file already downloaded.")
        
        album = metadata['album']
        artist = metadata['artist']
        print(f"Creating album directory for {album}.")
        album_path = f".\\audios\\{artist} - {album}"
        try:
            os.mkdir(album_path)
            print("Done. Saving songs...")
        except FileExistsError:
            print("Directory already exists, saving inside existing directory...")

        # Check if MP3 file exists, if not convert MP4
        audio_path = f"{album_path}\\{album} - Track {track_number}.mp3"
        if not os.path.exists(audio_path):
            print("\nConverting to MP3...")
            with VideoFileClip(tube_path) as video:
                video.audio.write_audiofile(audio_path)
        else:
            print("MP3 file already exists.")

        print("Appending metadata to MP3 file...")
        file = EasyID3(audio_path)
        metadata = tube[2]
        for k in metadata.keys():
            if k == "tags" or not metadata[k]:
                continue
            else:
                file[k] = metadata[k]
        file.save()
        print("Done.")
        
        track_number += 1

    elif len(tube) == 3 and not track_list_album:
        title = tube[2]["title"]
        video_title = tube[0].title
        print("\nHandling one track:")
        print("Artist:", tube[2]["artist"])
        print("Title:", title)
        
        # Check if MP4 exists, if not download it
        tube_path = f".\\videos\\{video_title}.mp4"
        if not os.path.exists(tube_path):
            print("Downloading...")
            tube_path = tube[0].streams.first().download(output_path = ".\\videos\\")
            print("Download successful. Video file located at {}".format(tube_path))
        else:
            print("MP4 file already downloaded.")
        
        # Check if MP3 file exists, if not convert MP4
        audio_path = f".\\audios\\{title}.mp3"
        if not os.path.exists(audio_path):
            print("\nConverting to MP3...")
            with VideoFileClip(tube_path) as video:
                video.audio.write_audiofile(audio_path)
        else:
            print("MP3 file already exists.")

        print("Appending metadata to MP3 file...")
        audio_path = f".\\audios\\{title}.mp3"
        file = EasyID3(audio_path)
        metadata = tube[2]
        for k in metadata.keys():
            if k == "tags" or not metadata[k]:
                continue
            else:
                file[k] = metadata[k]
        file.save()
        print("Done.")

    else:
        album = tube[2]["album"]
        video_title = tube[0].title
        print(f"\nHandling one album with {len(tube[3])} tracks:")
        print("Artist:", tube[2]["artist"])
        print("Album:", album)
        
        # Check if MP4 exists, if not download it
        tube_path = f".\\videos\\{video_title}.mp4"
        if not os.path.exists(tube_path):
            print("Downloading...")
            tube_path = tube[0].streams.first().download(output_path = ".\\videos\\")
            print("Download successful. Video file located at {}".format(tube_path))
        else:
            print("MP4 file already downloaded.")
        
        # Check if MP3 file exists, if not convert MP4
        audio_path = f".\\audios\\{album}.mp3"
        if not os.path.exists(audio_path):
            print("\nConverting to MP3...")
            with VideoFileClip(tube_path) as video:
                video.audio.write_audiofile(audio_path)
        else:
            print("MP3 file already exists.")
            
        print("Initiating album split...")
        song = AudioSegment.from_file(audio_path, "mp3")
        # Loop through tracks and extract appropriate section of full album audio file then append it to tracks_audio
        tracks = tube[3]
        tracks_audio = []
        for idx, track  in zip(range(len(tracks)), tracks):
            begin_stamp = track[1]
            # If song is last, time stamp is begin stamp to end of full album audio file, else end stamp is begin stamp of next song
            if idx == len(tracks) - 1:
                track = song[begin_stamp:]
            else:
                end_stamp = tracks[idx+1][1]
                track = song[begin_stamp:end_stamp]
            tracks_audio.append(track)
            
        # Clean file extract and metadata increment
        metadata = tube[2]
        album = metadata['album']
        artist = metadata['artist']
        print(f"Creating album directory for {album}.")
        album_path = f".\\audios\\{artist} - {album}"
        
        try:
            os.mkdir(album_path)
            print("Done. Saving songs...")
        except FileExistsError:
            print("Directory already exists, saving inside existing directory...")
            
        for idx, audio in zip(range(len(tracks_audio)), tracks_audio):
            track_name = tracks[idx][2]
            file_name = f"{album} - Track {idx+1}"
            audio_path = f"{album_path}\\{file_name}.mp3"
            audio.export(audio_path, format="mp3")
            audio_mp3 = EasyID3(audio_path)
            for k in metadata.keys():
                if k == "tags" or not metadata[k]:
                    continue
                else:
                    audio_mp3[k] = metadata[k]
            audio_mp3["title"] = track_name
            audio_mp3["tracknumber"] = str(idx + 1)
            audio_mp3.save()
            print(f"Extracted track #{idx + 1} - {track_name}")
            
        print("All done. Deleting intial album MP3 file...")
        os.remove(f".\\audios\\{album}.mp3")
        print(f"All done. Album can be found at {album_path}.")

print("All tube(s) have been extracted. Exiting...")