# Genius Lyrick Scraper



## Preparation Before Usage

###Spotify Keys
- You need to export your spotify API tokens
- These keys are random, you need to get your own from Spotify.
```python
	export SPOTIPY_CLIENT_ID=2387193yh123h19283120p31ho23
	export SPOTIPY_CLIENT_SECRET=3214823y4p9283y423h4o23
```

### Downloading Fastext Model
- You need to download <a href="https://fasttext.cc/docs/en/language-identification.html" target="_blank">`lid.176.bin`</a> from FastText in order to clean the lyrics later on.
- Just leave on the same folder as the repo

---

## Usage

### Scrapping Lyrics

```python
python3 --genius-token = "INSERT YOUR GENIUS TOKEN HERE"
```

### Cleaning Scrapped Lyrics

```python
python3 --clean-lyrics=True
```


## Aditional Information

- You can change the genre downloaded by editing choosen_categories in get_artists(). You need to manualy inspect the categories returned. Look into raw_categories


# Reference this is if you use it
