import csv
import random
import spotipy
import csv
import fasttext
import os
import pandas as pd
import numpy as np
import argparse
from os import path
from tqdm import tqdm
from os import listdir
from os.path import isfile, join
from spotipy.oauth2 import SpotifyClientCredentials
from GeniusArtistDataCollect import GeniusArtistDataCollect



def get_artists(filename = "data/artists.pkl"):
        """
        Creates and Pickles a Dataframe containing unique artists and their Genre. It's based on the assumption that artists have a single genre
        :param filename: str - Path to were the file is saved
        """

        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

        column_names = ["artist", "genre"]
        artist_df = pd.DataFrame(columns=column_names)

        raw_categories = sp.categories(limit = 50)

        #These were picked manualy by inspecting raw_categories
        choosen_categories = ['hiphop','rock','roots','soul','metal','rnb','indie_alt','latin','reggae'] 
        categories = [(cat['name'],cat["id"]) for cat in raw_categories['categories']["items"]]

        # Goes over choosen DIRECTORIES and gets corresponding PLAYLISTS
        # Goes over PLAYLISTS and gets ARTISTS by inspecting TRACKS
        for category_name,category_id in tqdm(categories):
            if category_id not in choosen_categories:
                continue

            categories_playlist = sp.category_playlists(category_id=category_id, limit=50)
            playlist_id = [playlist['id'] for playlist in  categories_playlist['playlists']['items']]
            raw_tracks = [sp.playlist_tracks(playlist_id=id_, limit=50) for id_  in playlist_id]
            for refs in raw_tracks:
                for tracks in refs['items']:
                    if tracks['track'] is not None and tracks['track']['artists'][0]['name'] not in artist_df["artist"].unique():
                        artist_df = artist_df.append({
                            'artist': tracks['track']['artists'][0]['name'],
                            'genre': category_name}
                            , ignore_index=True)

        with open(filename, "wb") as pickle_file:
            artist_df.to_pickle(pickle_file)


def scrape_artist_lyrics(genius_token,artistname,genre):
    '''
        :param genius_token: str - Get the token from Genius API
        :param filename: str - Artists name Eg."Nick Drake"
        :param genre: Only matters if want to give one genre per artist. 
                    Depends on the usage of GeniusArtistDataCollect look into https://github.com/miguelvalente/MusicAnalysis
    '''
    token = genius_token
    g = GeniusArtistDataCollect(token, artistname)
    songs_df = g.get_artist_songs(genre)
    if not isinstance(songs_df, pd.DataFrame):
        print(f"{artistname} failed it's extraction")
        return False

    return songs_df

    
def scrape_all_lyrics(genius_token, filename = "data/lyrics.csv", artists = "data/artists.pkl"):
    with open(artists, "rb") as pkl_file:
            artists = pd.read_pickle(pkl_file)

    if path.exists("data/lyrics.csv"):
        with open(filename, "r", encoding="utf-8",) as csv_lyrics:
            reader = csv.reader(csv_lyrics, delimiter='|')
            scrapped_artists = np.unique([row.to_list()[0] for row in reader])
    
    column_names = ["title","artist","lyrics","genre"]
    with open(filename, "a+", encoding="utf-8",newline="") as all_lyrics:
        data_csv_writer = csv.writer(all_lyrics, delimiter="|", quoting=csv.QUOTE_MINIMAL)
        for idx, row in artists.iterrows():        
            artist_lyrics = scrape_artist_lyrics(genius_token,row['artist'],row['genre'])
            if not isinstance(artist_lyrics, pd.DataFrame) or row['artist'] in scrapped_artists:
                continue
            data_csv_writer.writerows([row.to_list() for idx, row in artist_lyrics.iterrows()])

def clean_lyrics(lyrics_path = "data/lyrics.csv", clean_lyrics_path="data/clean_lyrics.pkl"):
    '''
        Cleans the raw lyrics.csv file. Removes Non English Lyrics, Empty Lyrics and Lyrics shorter then 350 characters
        
        IMPORTANT: You need to download lid.176.bin otherwise the method won't work https://fasttext.cc/docs/en/language-identification.html
    '''
    
    
    column_names = ["title","artist","text","genre"]

    with open(lyrics_path,"r") as csv_lyrics:
        df = pd.read_csv(csv_lyrics, delimiter='|', names=column_names)
    
    df["text"] = df["text"].str.replace("\[\*\]",'\n',)
    not_string = 0
    not_english = 0
    
    assert(path.exists("lid.176.bin"),"You need to download lid.176.bin to be able to clean the data\n https://fasttext.cc/docs/en/language-identification.html")

    model = fasttext.load_model('lid.176.bin')
    
    print(df.groupby(["genre"]).count())

    for idx, row in tqdm(df.iterrows(), desc ="Cleaning  Songs", leave = False, disable = False):
        if isinstance(row["text"],str):
            if len(row["text"]) < 350:
                df.drop(index = idx, inplace = True)
            elif not model.predict(row["text"].replace("\n"," "), k=1)[0][0] == "__label__en":
                not_english += 1
                df.drop(index = idx, inplace = True)
        else:
            not_string += 1
            df.drop(index = idx, inplace = True)

    print(f"\nLyrics were cleaned with Empty Lyrics: {not_string} and Non English Lyrics: {not_english}")
    print(df.groupby(["genre"]).count())

    
    with open(clean_lyrics_path, "wb") as pkl_file:
        df.to_pickle(pkl_file)
    
    print(f"Clean lyrics saved to {clean_lyrics_path}")


def main(args):

    data_path = "data"

    try:
        os.mkdir(data_path)
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path)

    if not path.exists("data/artists.pkl"):
        get_artists()
        print("Artists scrapped successfully")
    else:
        print("Artists have been scrapped")

    if args.clean_lyrics:
        clean_lyrics()
    else:
        scrape_all_lyrics(args.genius_token)


    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--genius-token",type=str, help="You need to get a API token from Genius Website",  required = True)
    parser.add_argument("--clean-lyrics", type=bool, help = "It cleans existing lyrics, removes non english lyricks and lyrics smaller then 350 characters", required = False, default = False)
    args = parser.parse_args()
    main(args)
