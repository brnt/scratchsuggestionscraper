# scratchsuggestionscraper
A web spider that suggests ways an organization could use Scratch based on website content.
Designed to integrate with Scratch's new Wordpress website. Uses regexs and BeautifulSoup 
to search a website for certain features (embedded Spotify player, links to external music
stores, etc.) and generates suggestions regarding how the website owner could implement 
our payment platform.

Also includes a simple web interface built in Flask.  This will probably have to run behind a more
robust server such as Gunicorn.
