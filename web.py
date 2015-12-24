import os
import requests
from scraper import Website
from flask import Flask, request, render_template
from flask.ext.cors import cross_origin
app = Flask(__name__)

@app.route('/')
@cross_origin()
def getSuggestions():
    if request.args.get('url'):
        url = request.args.get('url')
        site = Website(url)
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
                print url + " successfully logged in Pipedrive!"
            else:
                print "Couldn't log " + url + " in Pipedrive!"
                print "Pipedrive error: " + r.json()['error']
        except:
            print "Couldn't connect to Pipedrive!"
        return render_template("suggestions.html", suggestions=suggestions)
    else:
        return render_template("index.html")

@app.route('/loader')
def displayLoader():
    return render_template("loader.html");

if __name__ == '__main__':
    app.run(threaded=True)
