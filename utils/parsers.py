import re
from pytube import YouTube

# Parsers utility functions
def read_urls(text_file):
    with open(".\\inputs\\" + text_file, "r") as file:
        contents = file.read().split("\n")

    validation = []
    metadata = {}
    album = False
    track_number = 1
    for line in contents:
        if line[:5] == "album":
            album_line = line.split(">")
            if album_line[0].split(":")[1].strip() == "True":
                album = True

                album_md = album_line[1].strip().split(";;")
                # Check if template values have changed, if yes, add metadata
                if album_md[0] != "album":
                    metadata["album"] = album_md[0]
                if album_md[1] != "artist":
                    metadata["artist"] = album_md[1]
                if album_md[1] != "year":
                    metadata["date"] = album_md[2]

        elif line[:4] == "http":
            s_line = line.split(";;")

            # Check if template values have changed, if yes, add metadata
            song_metadata = {}
            if album:
                song_metadata["tracknumber"] = str(track_number)
                track_number += 1
                for k in metadata:
                    song_metadata[k] = metadata[k]
                song_metadata["title"] = s_line[2]
                if "artist" not in song_metadata.keys():
                    song_metadata["artist"] = s_line[4]
            else:
                if s_line[1] != "track_number":
                    song_metadata["tracknumber"] = s_line[1]
                if s_line[2] != "title":
                    song_metadata["title"] = s_line[2]
                if s_line[3] != "album":
                    song_metadata["album"] = s_line[3]
                if s_line[4] != "artist":
                    song_metadata["artist"] = s_line[4]
                if s_line[5] != "year":
                    song_metadata["date"] = s_line[5]

            if song_metadata:
                validation.append([YouTube(s_line[0]), s_line[0], song_metadata])
            else:
                validation.append([YouTube(s_line[0]), s_line[0], None])

            print(f"Added {validation[-1][0].title}.")

    return validation


def read_tracklist(text_file):
    with open(".\\inputs\\" + text_file, "r") as file:
        contents = file.read().split("\n")
    metadata = []
    for line in contents:
        s_line = line.split(";;")
        metadata.append(s_line[0], ts_decompose(s_line[1]), s_line[2])
    return metadata


def find_date(string_list):
    date = None
    for tag in string_list:
        if len(tag) == 4:
            try:
                int_date = int(tag)
                date = str(int_date)
            except:
                continue
    return date


def extract_string(line, 
                   start_flag, 
                   end_flag = None,
                   extract_list = None):
    
    if start_flag == "(":
        end_flag = ")"
    elif start_flag == "[":
        end_flag = "]"
    #print(end_flag)
    if not end_flag:
        end_flag = start_flag
    
    if not extract_list:
        extract_list = []
    
    if start_flag not in line:
        return extract_list
    
    for c in line:
        if c == start_flag:
            #print(c)
            s_idx = line.index(c)
            for d in line[s_idx+1:]:
                if d == end_flag:
                    #print(d)
                    e_idx = line[s_idx+1:].index(d) + len(line[:s_idx+1])
                    break
            extract_list.append(line[s_idx+1:e_idx])
            new_line = line[e_idx+1:]
            #print(new_line)
            return extract_string(new_line, start_flag, end_flag, extract_list)


def ts_decompose(ts):
    stamps = ts.split(":")
    if len(stamps) == 3:
        hours = int(stamps[0])
        mnts = int(stamps[1])
        secs = int(stamps[2])
        mls = hours*60*60*1000 + mnts*60*1000 + secs*1000
    else:
        mnts = int(stamps[0])
        secs = int(stamps[1])
        mls = mnts*60*1000 + secs*1000
    return mls


def strip_string(line):
    flags = ["-", "–", "|", ":"]
    for flag in flags:
        line = line.replace(flag, " ")
    line = line.strip().strip(".").strip()
    return line


# Main parsers: Title and tracklist from description
# Parse_title will return a dictionary with the parsed metadata, fields not found will be NoneTypes.
def parse_title(title, album):
    artist = None
    date = None
    tags = None
    tracknumber = None
    final_title = None
    flags_tag = ["[", "("]
    flags_title = ["-", "–", "|"]
    tracknum_format = ["[ABCDEFGH][0-9]", "[0-9][0-9]\.", "[0-9][0-9]\ ", "[0-9]\.", "[0-9]\ "]
    tracknum = None

    # Search for a track number in the new line
    for f in tracknum_format:
        search = re.search(f, title)
        if search:
            #print(f)
            tracknum = search
            break
    
    if tracknum:
        span = tracknum.span()
        tags_title = title[:span[0]] + title[span[1]:]
        tracknumber = title[span[0]:span[1]].strip()
    else:
        tags_title = title
    
    tags = []
    for flag in flags_tag:
        temp_tags = extract_string(tags_title, flag)
        if temp_tags:
            tags += temp_tags

    # Generate new title by removing tags from original string
    n_title = tags_title
    for c in tags_title:
        if c in flags_tag:
            n_title = tags_title[:tags_title.index(c)]
            break
    
    # Extract date from tags
    date = find_date(tags)
    # If not in tags, search in title
    if not date:
        date = find_date(title.split())
        # If not in title, search within each tag
        if not date:
            for tag in tags:
                #print(tag.split())
                date = find_date(tag.split())
                if date:
                    break

    if date:
        # Remove from tags
        if date in tags:
            tags.pop(tags.index(date))

        # Remove from title
        if date in n_title:
            #print(date)
            #print(n_title.find(date))
            #print(n_title[:n_title.find(date)], "//", date, "//", n_title[n_title.find(date)+3:])
            new_title = n_title[:n_title.find(date)] + n_title[n_title.find(date)+4:]
        else:
            new_title = n_title
    else:
        new_title = n_title

    
    # Generate artist and clean title
    for tag in flags_title:
        temp_title = new_title.split(tag)
        if len(temp_title) > 1:
            artist = temp_title[0].strip()
            final_title = temp_title[1].strip()

    
    # Return final values
    metadata = {
        "artist": artist,
        "title" : final_title,
        "album" : None,
        "date" : date,
        "tracknumber": tracknumber,
        "tags" : tags
    }
    if album:
        metadata["album"] = metadata["title"]
        metadata["title"] = None
    #print(" Artist: ", artist, "\n",
          #"Title: ", final_title, "\n",
          #"Date: ", date, "\n",
          #"Tags: ", tags, "\n")
    
    return metadata


# Parse_tracklist will return a list with the parsed track list or an empty list if no track list is found.
def parse_tracklist(description):
    # Initialize local variables
    ts_format = ["[0-9]:[0-9][0-9]:[0-9][0-9]", "[0-9]:[0-9][0-9]"]
    tracknum_format = ["[ABCDEFGH][0-9]", "[0-9]\.", "[0-9]\ ", "[0-9][0-9]\.", "[0-9][0-9]\ "]
    TS = {}
    TN = {}
    titles = {}
    span_idx = []
    desc = description.split("\n")
    for idx, line in zip(range(len(desc)), desc):
        # Init
        new_line = None
        ts_search = None
        tracknum = None

        # Search for a timestamp in the current line
        for fmt in ts_format:
            if not ts_search:
                ts_search = re.search(fmt, line)       

        if ts_search:
            # If timestamp is detected, extract it from the line and create a new line without it
            span = ts_search.span()
            span_idx.append(span[1])
            if span[0] == 0:
                span = [1, span[1]]
            #print(line[span[0]-1: span[1]+1])
            TS[idx] = str(line[span[0]-1: span[1]]).replace(" ", "0")
            new_line = line[:span[0]-1] + line[span[1]+1:]
        else:
            # If no timestamp is detected, pass on to the next line
            continue
        
        # Search for a track number in the new line
        for f in tracknum_format:
            search = re.search(f, new_line)
            if search:
                #print(f)
                tracknum = search
                break
        
        # If track number is found, extract it from the line
        if tracknum:
            span_track = tracknum.span()
            #print(new_line[span_track[0]: span_track[1]])
            TN[idx] = new_line[span_track[0]: span_track[1]]
        
        # Parse the title from the line depending on track number and timestamp positions
        if not tracknum:
            title = strip_string(new_line)
            titles[idx] = title
        elif span_track[0] < (len(new_line)/2):
            title = strip_string(new_line[span_track[1]:])
            titles[idx] = title
        else:
            title = strip_string(new_line[:span_track[0]])
            titles[idx] = title
    
    # Compile collected metadata and return final value
    metadata = []
    if len(titles) == len(TS):
        for idx, k in zip(range(1, len(titles)+1), titles.keys()):
            stamp = ts_decompose(TS[k])
            metadata.append([idx, stamp, titles[k]])
            #print([idx, TS[k], titles[k]])
        return metadata
    elif len(titles) == len(TS)+1:
        # This case is for when no "00:00" timestamp is provided
        for idx, k in zip(range(1, len(titles)+1), titles.keys()):
            if idx == 1:
                metadata.append([idx, 0, titles[k]])
                continue
            else:
                stamp = ts_decompose(TS[k])
                metadata.append([idx, stamp, titles[k]])
        return metadata
    else:
        #print("ParsingError: could not match timestamps with titles. {x} timestamps found, {y} titles found.".format(x = len(TS), y = len(titles)))
        return []