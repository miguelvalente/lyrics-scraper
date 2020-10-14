import os
import re
import requests
import pandas as pd
import urllib.request
from bs4 import BeautifulSoup

class GeniusArtistDataCollect:
    """A wrapper class  forked from https://github.com/benfwalla/MusicAnalysis.git 
    retrieve, clean, and organize all the songs of a given artist.
    
    FORK CHANGES:
        * Due to the way GeniusApi works the original wrapper wasn't working anymore so I made a 
        changed to CSS selectors in the webscrapping portion.
        * I've added a function that retrieves the genre of the song, it does not always work due to the way Genius API works and 
        if that is the case the genre will have a [failed] flag. A genre can be infered from the most common one for each artist8
        

    Uses the Genius API and webscraping techniques to get the data."""

    def __init__(self, client_access_token, artist_name):
        """
        Instantiate a GeniusArtistDataCollect object
        :param client_access_token: str - Token to access the Genius API. Create one at https://genius.com/developers
        :param artist_name: str - The name of the artist of interest
        """
        self.client_access_token = client_access_token
        self.artist_name = artist_name
        self.base_url = 'https://api.genius.com/'
        self.headers = {'Authorization': 'Bearer ' + self.client_access_token}
        self.artist_songs = None

    def search(self, query):
        """Makes a search request in the Genius API based on the query parameter. Returns a JSON response."""
        request_url = self.base_url + 'search'
        data = {'q': query}
        response = requests.get(request_url, data=data, headers=self.headers).json()
        return response

    def get_artist_songs(self,genre = "[Not Provided]"):
        """
        Gets the songs of self.artist_name and places in a pandas.DataFrame
        :param genre: I use this wrapper providing one genre per artist. 
        This parameter is unused if you use the method get_genre to get genres for each song
        """
        # Search for the artist and get their id
        search_artist = self.search(self.artist_name)

        #Prevents the stoppage in case of an Artist having zero lyrics on Genius
        if len(search_artist['response']['hits']) == 0:
            return False
            
        artist_id = str(search_artist['response']['hits'][0]['result']['primary_artist']['id'])
        print("ID: " + artist_id)
        # Initialize DataFrame
        df = pd.DataFrame(columns=['title', 'url'])
        # Iterate through all the pages of the artist's songs
        more_pages = True
        page = 1
        i = 0
        while more_pages:
            # Make a request to get the songs of an artist on a given page
            request_url = self.base_url + 'artists/' + artist_id + '/songs' + '?per_page=50&page=' + str(page)
            response = requests.get(request_url, headers=self.headers).json()

                # For each song which the given artist is the primary_artist of the song, add the song title and
                # Genius URL to the DataFrame
            for song in response['response']['songs']:
                if str(song['primary_artist']['id']) == artist_id:
                    title = song['title']
                    url = song['url']
                    df.loc[i] = [title, url]
                    i += 1
                page += 1

            if response['response']['next_page'] is None:
                more_pages = False

    
        # Get the HTML and Song Lyrics from helper methods in the class
        df['artist'] = self.artist_name
        df['html'] = df['url'].apply(self.get_song_html)
        df['lyrics'] = df.apply(lambda row: self.get_lyrics(row.html), axis=1)
        #Uncomment to use the genre method otherwise
        #df['genre'] = df.apply(lambda row: self.get_genre(row.html), axis=1)
        df['genre'] = genre
        
        del df['url']
        del df['html']

        self.artist_songs = df

        return self.artist_songs

    def get_song_html(self, url):
        """Scrapes the entire HTML of the url parameter"""
        request = urllib.request.Request(url)
        request.add_header("Authorization", "Bearer " + self.client_access_token)
        request.add_header("User-Agent",
                           "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'")

        page = urllib.request.urlopen(request)
        html = BeautifulSoup(page, "lxml")
        print("Scraped: " + url)
        return html


    def get_lyrics(self, html):
        """Scrapes the html parameter to get the song lyrics on a Genius page in one, large String object"""
        #gets lyricks trough a css selector
        raw_lyrics = html.select('div[class*="Lyrics__Container"]')
        if len(raw_lyrics) == 0:
            raw_lyrics = html.select('div[class="lyrics"]')

        lyrics =  []            
        for lyric in raw_lyrics:
            temp_lyrics = re.sub(r'[\(\[].*?[\)\]]', '', lyric.get_text()).strip()
            temp_lyrics = re.sub('\n+', '', temp_lyrics)
            lyrics.append(re.findall('[A-Z][^A-Z]*', temp_lyrics))

        all_words = ''
        # Format lyrics 
        for section in lyrics:
            if len(section) == 0:
                continue

            for verse in section:
                all_words += verse.strip() + "[*]"
            
        return all_words

    #Gets the genres of a particular song
    def get_genre(self,html):
        raw_genres = html.select('img[src*="genres"]')
        if len(raw_genres) != 0:
            raw_genres = raw_genres[0].attrs['src']

            raw_genres = raw_genres.split("page-genres=",1)[1].split("+Genius",1)[0]
            genres = raw_genres.split("%2C")
        else:
            genres = ["failed"]
            
        return genres