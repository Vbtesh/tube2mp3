# tube2mp3
YouTube converter command line app. Aimed at music video. It attempts to parse the title and the description for metadata

Features:

- Take in one (in command-line) or multiple urls (user the prescribed .txt format)
- Parses title for metadata
- Albums: if a tracklist is provided or is parsable in the description, it will return a folder with all individual tracks as separate .mp3 files

To Do:

- Handle playlists
- Split audio on silence: the basic algorithm works but is really imprecise for tracks that are seperate on the album but are not divided by a specific silence
- Integrate it in a Django Web-App: opportunity to learn the framework and make it available to others

