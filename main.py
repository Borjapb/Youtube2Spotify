
import json
import requests
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import youtube_dl

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


class ABC:
    def __init__(self):
        self.spotify_token = 'TOKEN_A_COMPLETAR'
        self.spotify_user_id = 'USER_ID_A_COMPLETAR'
        self.ytPlaylist_id = 'YT_PLAYLIST_ID_A_COMPLETAR'
        self.youtube_client = None
        self.all_song_info = {}

    def get_youtube_client(self):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        self.youtube_client = googleapiclient.discovery.build(
            api_service_name,
            api_version,
            credentials=credentials
        )

    def get_yt_playlist_videos(self):

        self.get_youtube_client()

        request = self.youtube_client.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=50,
            playlistId=self.ytPlaylist_id
        )
        response = request.execute()

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = 'https://www.youtube.com/watch?v={}'.format(item["contentDetails"]["videoId"])

            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)

            song_name = video["track"]
            artist = video["artist"]

            if self.get_spotify_uri(song_name, artist) is None:
                continue

            self.all_song_info[video_title] = {
                "song_name": song_name,
                "artist": artist,
                "spotify_uri": self.get_spotify_uri(song_name, artist)
            }

    # Create the playlist to store all the songs of Youtube
    def create_playlist(self):
        body = json.dumps({
            "name": "Youtube_playlist",
            "public": True
        })

        response = requests.post(
            'https://api.spotify.com/v1/users/{}/playlists'.format(self.spotify_user_id),
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()

        return response_json["id"]

    # Get the uri of the song by name and artist
    def get_spotify_uri(self, song_name, artist):
        query = 'https://api.spotify.com/v1/search?q=track%3A{}+artist%3A{}&type=track'.format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]
        if len(songs) != 0:
            uri = songs[0]["uri"]
            return uri
        else:
            return None

    def add_song_to_playlist(self):

        self.get_yt_playlist_videos()

        uris = []
        for song, info in self.all_song_info.items():
            uris.append(info["spotify_uri"])

        playlist_id = self.create_playlist()

        query = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(playlist_id)
        response = requests.post(
            query,
            headers={
                "Authorization": "Bearer {}".format(self.spotify_token)
            },
            data=json.dumps(uris)
        )


p = ABC()
ABC.add_song_to_playlist(p)
