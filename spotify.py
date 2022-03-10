# Import Libraries

#pip install spotipy
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import requests
import time
import pandas as pd
import json
import boto3
from decimal import Decimal
from scipy import spatial

# Define Variables for spotify oauth access
cid = 'cddc6473eb374defb1c9c5a34d730ebb'
secret = 'f53e9095874645a690a3d1e682ef8ab7'
redirect = 'https://spotify-analytics-j1mk1m.herokuapp.com/'
scope = "user-library-read user-top-read user-read-recently-played playlist-modify-private playlist-modify-public"

def get_sp():
# create spotify object using authentication from user
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret,redirect_uri=redirect, scope=scope))
    return sp

def get_current_user_information(sp, df_user_playlist, df_user_recent, df_user_top_artists, df_user_top_tracks):
    playlists = sp.current_user_playlists()['items']
    for playlist in playlists:
        df_user_playlist = df_user_playlist.append({'playlist_name':playlist['name'], 'playlist_id':playlist['id'], 'owner_id':playlist['owner']['id'], 'url':playlist['external_urls']['spotify']}, ignore_index=True)
    recents = sp.current_user_recently_played(limit=20)['items']
    for recent in recents:
        df_user_recent = df_user_recent.append({'track_name':recent['track']['name'], 'track_id':recent['track']['id'], 'artist_name':recent['track']['artists'][0]['name'], 'track_url':recent['track']['external_urls']['spotify']}, ignore_index=True)
    top_artists = sp.current_user_top_artists(limit=20)['items']
    for artist in top_artists:
        df_user_top_artists = df_user_top_artists.append({'artist_name':artist['name'], 'artist_id':artist['id'], 'artist_url':artist['external_urls']['spotify']}, ignore_index=True)
    top_tracks = sp.current_user_top_tracks(limit=20)['items']
    for track in top_tracks:
        df_user_top_tracks = df_user_top_tracks.append({'track_name':track['name'], 'track_id':track['id'], 'artist_name':track['artists'][0]['name'], 'track_url':track['external_urls']['spotify']}, ignore_index=True)
    return df_user_playlist, df_user_recent, df_user_top_artists, df_user_top_tracks

def create_user_data_csv():
    # Get Access to Spotify API
    sp = get_sp()
    # Create current user dataframes
    df_user_playlist = pd.DataFrame(columns=['playlist_name', 'playlist_id', 'owner_id', 'url'])
    df_user_recent = pd.DataFrame(columns=['track_name', 'track_id', 'artist_name', 'track_url'])
    df_user_top_artists = pd.DataFrame(columns=['artist_name', 'artist_id', 'artist_url'])
    df_user_top_tracks= pd.DataFrame(columns=['track_name', 'track_id', 'artist_name', 'track_url'])

    df_user_playlist, df_user_recent, df_user_top_artists, df_user_top_tracks = get_current_user_information(sp, df_user_playlist, df_user_recent, df_user_top_artists, df_user_top_tracks)
    df_user_playlist.to_csv("user_playst.csv")
    df_user_recent.to_csv("user_recent.csv")
    df_user_top_artists.to_csv("user_top_artists.csv")
    df_user_top_tracks.to_csv("user_top_tracks.csv")

def add_track_to_database(sp, table, track):
    table.put_item(Item={
            'track_id': track['id'],
            'name' : track['name'],
            'artist' : track['artists'][0]['name'],
            'artist_id' : track['artists'][0]['id'],
            'url' : track['external_urls']['spotify'],
            'popularity' : track['popularity'],
            'album_id' : track['album']['id'],
            'album' : track['album']['name'],
            'duration_ms' : track['duration_ms']
        }, ConditionExpression="attribute_not_exists(track_id)")
    features = sp.audio_features([track['id']])[0]
    table.update_item(
            Key={
                'track_id': track['id']
            },
            UpdateExpression = "set acousticness=:a, danceability=:d, energy=:e, instrumentalness=:i, liveness=:li, loudness=:lo, modality=:m, speechiness=:s, tempo=:t, valence=:v",
            ExpressionAttributeValues={
                ':a': Decimal(""+str(features['acousticness'])),
                ':d': Decimal(""+str(features['danceability'])),
                ':e': Decimal(""+str(features['energy'])),
                ':i': Decimal(""+str(features['instrumentalness'])),
                ':li': Decimal(""+str(features['liveness'])),
                ':lo': Decimal(""+str(features['loudness'])),
                ':m': features['mode'],
                ':s': Decimal(""+str(features['speechiness'])),
                ':t': Decimal(""+str(features['tempo'])),
                ':v': Decimal(""+str(features['valence'])) 
            }  
    )

def add_tracks_to_database(sp, table, tracks):
    for track in tracks:
        add_track_to_database(sp, table, track)


def get_current_user_saved_tracks(sp):
    #get saved tracks of current user
    response = sp.current_user_saved_tracks(limit=20)
    tracks = []
    for track in response['items']:
        tracks.append(track['track'])
    while (response['next']):
        response = sp.next(response)
        for track in response['items']:
            tracks.append(track['track'])
    return tracks

def get_top_tracks(sp, table):
    top_tracks = sp.current_user_top_tracks(limit=20)['items']
    return top_tracks

def get_playlist_pool(sp, items):
    # item could be: tracks, artists, albums, or keywords
    playlists = []
    for item in items:
        playlists.extend(sp.search(item['name'], limit=20, type='playlist')['playlists']['items'])
    return playlists

def get_playlist_pool_from_keyword(sp, keyword):
    response = sp.search(keyword, limit=50, type='playlist')['playlists']
    playlists = response['items']
    count = 0
    while (count < 4 and response['next']):
        response = sp.next(response)
        playlists.extend(response['items'])
    return playlists

def get_track_ids_from_playlist_pool(sp, table, playlists):
    track_ids = []
    for playlist in playlists:
        response = sp.playlist_tracks(playlist['id'])['items']
        for track in response:
            if (track['track']):
                add_track_to_database(table, track['track'], sp)
                track_ids.append(track['track']['id'])
    return track_ids

def get_top_tracks_by_count(track_ids, limit):
    count = {}
    for id in track_ids:
        if id in count:
            count[id] = count[id]+1
        else:
            count[id] = 1
    count = sorted(count.items(), key=lambda kv:(kv[1], kv[0]), reverse=True)[0:limit]
    return count

def recommendation_single_item(sp, table, keyword):
    playlists = get_playlist_pool_from_keyword(sp, keyword)
    track_ids = get_track_ids_from_playlist_pool(sp, table, playlists)
    count = get_top_tracks_by_count(track_ids, 50)
    return [pair[0] for pair in count]

def recommendation_multiple_items(sp, table, items):
    # items can be a list of tracks, artists, albums, or keywords
    playlists = get_playlist_pool(sp, items)
    track_ids = get_track_ids_from_playlist_pool(sp, table, playlists)
    count = get_top_tracks_by_count(track_ids, 50)
    return [pair[0] for pair in count]

def get_features_from_dbtrack(track):
    return [float(track['acousticness']), float(track['danceability']), float(track['energy']), float(track['instrumentalness']), float(track['liveness']), float(track['loudness']), float(track['modality']), float(track['popularity']), float(track['speechiness']), float(track['tempo']), float(track['valence'])]

def get_similarity(feature_array1, feature_array2):
    return 1 - spatial.distance.cosine(feature_array1, feature_array2)

def get_top_similar_tracks(base_dbtracks, candidate_dbtracks):
    similarity_array = {}
    for ctrack in candidate_dbtracks:
        similarity = 0
        cfeature = get_features_from_dbtrack(ctrack)
        for btrack in base_dbtracks:
            bfeature = get_features_from_dbtrack(btrack)
            similarity += get_similarity(cfeature, bfeature)
        similarity_array[ctrack['track_id']] = similarity
    top_tracks = sorted(similarity_array.items(), key=lambda kv:(kv[1], kv[0]), reverse=True)
    return top_tracks

def retrieve_dbtracks(sp, table, tracks):
    dbtracks = []
    for track in tracks:
        response = table.get_item(Key={'track_id':track['id']})
        if ('Item' in response):
            dbtracks.append(response['Item'])
        else:
            add_track_to_database(sp, table, track)
    return dbtracks



def create_playlist(sp, track_ids, name):
    playlist_id = sp.user_playlist_create(sp.current_user()['id'], name)['id']
    sp.playlist_add_items(playlist_id, track_ids)

def main():
    sp = get_sp()

    # tracks = get_current_user_saved_tracks(sp)
    
    # Get dynamo database spotify tracks
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table("spotify_tracks")

    tracks = get_top_tracks(sp, table)
    base_dbtracks = retrieve_dbtracks(sp, table, tracks)
    saved_tracks = get_current_user_saved_tracks(sp)
    candidate_dbtracks = retrieve_dbtracks(sp, table, saved_tracks)
    top_tracks = get_top_similar_tracks(base_dbtracks, candidate_dbtracks)[0:70]
    create_playlist(sp, [track[0] for track in top_tracks], "Similar Tracks")

    
    




    

if __name__ == "__main__":
    main()
