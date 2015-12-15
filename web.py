from scraper import Website
from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def getSuggestions():
    if request.method == 'POST':
        url = request.form['website']
        site = Website(url)
        suggestions = site.getSuggestions()
        return render_template("suggestions.html", suggestions=suggestions)
    else:
        return render_template("index.html")

if __name__ == '__main__':
    app.run()