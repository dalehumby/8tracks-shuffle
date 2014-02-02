# 8tracks Shuffle - Download your favourite tracks for playing on the go

I love [8tracks](http://8tracks.com/). And I love listening to my music
while I am running or in the gym. Up to now I've used 8tracks' fantastic
iPhone app. But streaming music over 3G is expensive, and strapping a phone
to my arm is uncomfortable. Especially when compared to Apple's matchbook 
sized iPod Shuffle which holds 2G of music.

I wrote this 8tracks client uses the [API](http://8tracks.com/developers/api_v3)
to download and store played tracks locally for import in to iTunes and syncing
with my iPod.

The client is well behaved. It downloads the tracks as fast as if you were
really listening to them, and reports the songs as played at the 30s mark.

## Usage

The script needs some parameters to operate correctly.

1. You will need an [API key](http://8tracks.com/developers/new).
2. [Register a new user](http://8tracks.com/) so the script has credentials 
   to log in. 
   * If you want the script to follow you and download your liked mixes then
     don't use your own username and password. Your logged in session on the 
     website and the script will interfere with each other.
3. If you want the script to download the mixes you like then find your user ID.
   * On the 8tracks website, under Activity hover over Listening history and
     the URL at the bottom of your screen will be similar to
     http://8tracks.com/mix_sets/listened:123456789.
   * The number after the colon (e.g. 123456789) is your user ID.
4. Decide on a collection to follow. 
   * Could be 'liked' to download all mixes you clicked heart icon.
   * Or a specific collection of yours, such as 'gym' to 'ipod-shuffle'.


**Note:** I'm pretty sure downloading tracks for offline playing is against
8tracks T&C's. After a thorough reading I still couldn't find anything that
prohibited it. That said, your account/API key might be blocked if they
disagree.

## Todo's
1. The script isn't particularly robust, especially against http timeouts and
   error codes. This needs fixing.
2. Track metadata such as title, album, artist should be saved audio file.
3. Make playlists of mixes so importing to iTunes is better.
4. After all tracks in a mix have been downloaded auto-import to iTunes.