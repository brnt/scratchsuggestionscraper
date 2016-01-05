import os
import logging
import requests
from scraper import Website
from flask import Flask, request, render_template
from flask.ext.cors import cross_origin
app = Flask(__name__)

#configure local logger
logger = logging.getLogger(__name__)
streamhandler = logging.StreamHandler()
filehandler = logging.FileHandler("scraper.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%m/%d/%Y %I:%M:%S %p')
streamhandler.setFormatter(formatter)
filehandler.setFormatter(formatter)
logger.addHandler(streamhandler)
logger.addHandler(filehandler)
logger.setLevel(logging.INFO)

#configure scraper logger
logging.getLogger("scraper").addHandler(streamhandler)
logging.getLogger("scraper").addHandler(filehandler)
logging.getLogger("scraper").setLevel(logging.INFO)

@app.route('/')
@cross_origin()
def getSuggestions():
    if request.args.get('url'):
        url = request.args.get('url')
        site = Website(url)
        if site.loaded:
            suggestions = site.getSuggestions()

            # log search as deal in pipedrive
            token = os.environ.get("PIPEDRIVE_TOKEN")
            stage_id = '42'
            payload = {
                'title': url,
                'stage_id': stage_id,
                'visible_to': '3',
            }
            try:
                r = requests.post("https://api.pipedrive.com/v1/deals?api_token=" + token, data=payload)
                if r.json()['success']:
                    logger.info(url + " successfully logged in Pipedrive!")
                else:
                    logger.error("Couldn't log " + url + " in Pipedrive!")
                    logger.error("Pipedrive error: %s" % r.json()['error'])
            except IOError as e:
                logger.error("Couldn't connect to Pipedrive: %s" % e)
            return render_template("suggestions.html", suggestions=suggestions)
        else:
            return render_template("no_exist.html")
    else:
        return render_template("index.html")

@app.route('/loader')
def displayLoader():
    return render_template("loader.html");

if __name__ == '__main__':
    app.run(threaded=True)
