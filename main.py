import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import requests

from youtube_dl import YoutubeDL

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


class ABC:
    def __init__(self):
        self.youtube_client = None
        self.playlists = {}
        self.spotify_user_id = 'USER_ID_A_COMPLETAR'
        self.spotify_token = 'TOKEN_A_COMPLETAR'
        self.uris = []

    def get_YT_client(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secrets.json"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()
        self.youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

    def get_YT_playlists(self):
        self.get_YT_client()

        request = self.youtube_client.playlists().list(
            part="snippet",
            mine=True
        )
        response = request.execute()

        i = 1
        for item in response["items"]:
            self.playlists[item["snippet"]["title"]] = item["id"]
            print(str(i) + "." + " " + item["snippet"]["title"])
            i = i + 1
        while True:
            playlist = input("Choose a playlist: ")
            if playlist in self.playlists:
                break
        return playlist

    def get_videos_from_playlist(self):

        playlist = self.get_YT_playlists()

        request = self.youtube_client.playlistItems().list(
            part="snippet",
            playlistId=self.playlists[playlist],
            maxResults=50
        )
        response = request.execute()

        ydl = YoutubeDL()
        ydl.add_default_info_extractors()
        for item in response["items"]:
            info = ydl.extract_info(
                'http://www.youtube.com/watch?v='+item["snippet"]["resourceId"]["videoId"],
                download=False
            )
            uri = self.get_Spotify_song_uri(info["track"], info["artist"])
            if uri is None:
                continue

            self.uris.append(uri)

    def get_Spotify_song_uri(self, title, artist):
        query = "https://api.spotify.com/v1/search?q=track:{}%20artist:{}&type=track".format(title,artist)

        response = requests.get(
            query,
            headers={
                "Authorization": "Bearer " + self.spotify_token
            }
        )
        if len(response.json()["tracks"]["items"]) == 0:
            return None
        else:
            return response.json()["tracks"]["items"][0]["uri"]

    def create_Spotify_playlist(self):

        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.spotify_user_id)

        response = requests.post(
            query,
            data=json.dumps({
                "name": "Playlist de Youtube"
            }),
            headers={
                "Authorization": "Bearer " + self.spotify_token,
                "Content-Type": "application/json"
            }
        )

        return response.json()["id"]

    def add_songs_to_Spotify_playlist(self):

        self.get_videos_from_playlist()

        playlist_id = self.create_Spotify_playlist()
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data=json.dumps({
                "uris": self.uris
            }),
            headers={
                "Authorization": "Bearer " + self.spotify_token,
                "Content-Type": "application/json"
            }
        )


if __name__ == "__main__":
    p = ABC()
    ABC.add_songs_to_Spotify_playlist(p)
