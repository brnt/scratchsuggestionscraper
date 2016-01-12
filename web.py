import os
import logging
import requests
from scraper import Website
from urlmanip import URLManip
from flask import Flask, request, render_template, Response
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

def logToPipedrive(url):
    token = os.environ.get("PIPEDRIVE_TOKEN")
    filter_id = '24'
    stage_id = '42'

    try:
        # check if deal already exists
        exists = False
        r = requests.get("https://api.pipedrive.com/v1/deals?filter_id="+ filter_id + "&api_token=" + token)
        deals = r.json()
        for deal in deals['data']:
            if deal['title'] == url:
                logger.info("Not logging %s as deal in Pipedrive. Already exists." % url)
                exists = True

        # if it doesn't already exist, log search as deal in pipedrive
        if not exists:
            payload = {
                'title': url,
                'stage_id': stage_id,
                'visible_to': '3',
            }

            r = requests.post("https://api.pipedrive.com/v1/deals?api_token=" + token, data=payload)
            if r.json()['success']:
                logger.info(url + " successfully logged in Pipedrive!")
            else:
                logger.error("Couldn't log " + url + " in Pipedrive!")
                logger.error("Pipedrive error: %s" % r.json()['error'])

    except IOError as e:
        logger.error("Couldn't connect to Pipedrive: %s" % e)

    except:
        logger.error("Failed to log %s to Pipedrive." % url)

@app.route('/')
@cross_origin()
def getSuggestions():
    if request.args.get('url'):
        url = URLManip().cleanURL(request.args.get('url'))
        site = Website(url)
        if site.loaded:
            def generator():
                yield "<ul>"
                for suggestion in site.getSuggestions():
                    yield "<li>" + suggestion + "</li>"
                yield "</ul>"
                logToPipedrive(url)
            return Response(generator(), mimetype="text/html")
        else:
            return render_template("no_exist.html")
    else:
        return render_template("index.html")

@app.route('/loader')
def displayLoader():
    return render_template("loader.html");

if __name__ == '__main__':
    app.run(threaded=True)
