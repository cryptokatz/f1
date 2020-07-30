import feedparser as fp
import time
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import sys
import dateutil.parser as dp
import urllib3
import json
import sqlite3
import urllib
from bs4 import BeautifulSoup


def addItem(db, blog, id):
    add = 'insert into items (blog, id) values (?, ?)'
    db.execute(add, (blog, id))
    db.commit()


def clean_sitename(site_name):
    """This function returns the absolute
    value of the entered number"""

    s1 = site_name.replace("Formula 1 news - Autosport", "Autosport")
    s2 = s1.replace(" - the latest hottest F1 news", "")
    s3 = s2.replace("BBC Sport - Formula 1", "BBC Sport")
    s4 = s3.replace(" :: F1 Feed", "")
    s5 = s4.replace(" - Formula 1 - Stories","")
    return s5

def clean_headline(headline):
    sep = '|'
    rest = headline.split(sep, 1)[0]
    return rest

jsonsubscriptions = [
]

xmlsubscriptions = [
    'https://www.autosport.com/rss/feed/f1',
    'https://thejudge13.com/feed/',
    'http://feeds.bbci.co.uk/sport/formula1/rss.xml?edition=uk',
    'https://www.racefans.net/feed/',
    'https://www.jamesallenonf1.com/feed/',
    'https://racingnews.co/tag/formula-one/feed/',
    'https://joesaward.wordpress.com/feed/',
    'https://www.grandprix247.com/feed/',
    'https://www.motorsport.com/rss/f1/news/',
    'http://feeds.feedburner.com/daily-express-f1',
    'https://www.planetf1.com/feed/',
    #'http://feeds.feedburner.com/totalf1-recent',
    'https://www.pitpass.com/fes_php/fes_usr_sit_newsfeed.php?fes_prepend_aty_sht_name=1',
    'https://peterwindsor.com/feed/',
    'http://podcasts.skysports.com/podcasts/SkySportsF1/SkySportsF1.xml'
]

podcastsubscriptions = [
    'http://www.fastestlappodcast.com/feed/',
    'https://rss.acast.com/missedapex',
    'https://www.spreaker.com/show/2977992/episodes/feed',
    'http://podcasts.skysports.com/podcasts/SkySportsF1/SkySportsF1.xml'
]

videosubscriptions = [
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCB_qr75-ydFVKSF9Dmo6izg',
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCPwy2q7BNjdLYu1kM_OEJVw'
]

fp._HTMLSanitizer.acceptable_elements |= {'object', 'embed', 'iframe'}

db = sqlite3.connect('read-feeds.db')
db2 = sqlite3.connect('read-podcasts.db')
db3 = sqlite3.connect('read-videos.db')
query = 'select * from items where blog=? and id=?'

# Collect all unread posts and put them in a list of tuples. The items
# in each tuple are when, blog, title, link, body, n, and author.
posts = []
podcasts = []
videos = []
n = 0
n2 = 0
n3 = 0

# We're not going to accept items that are more than 3 days old, even
# if they aren't in the database of read items. These typically come up
# when someone does a reset of some sort on their blog and regenerates
# a feed with old posts that aren't in the database or posts that are
# in the database but have different IDs.
utc = pytz.utc
homeTZ = pytz.timezone('US/Central')
daysago = datetime.today() - timedelta(days=2)
daysago = utc.localize(daysago)
weekago = datetime.today() - timedelta(days=7)
weekago = utc.localize(weekago)


# NEWS FEEDS
for s in xmlsubscriptions:
    try:
        f = fp.parse(s)
        try:
            blog = f['feed']['title']
        except KeyError:
            blog = "---"
        for e in f['entries']:
            try:
                id = e['id']
                if id == '':
                    id = e['link']
            except KeyError:
                id = e['link']

            # Add item only if it hasn't been read.
            match = db.execute(query, (blog, id)).fetchone()
            if not match:

                try:
                    when = e['published_parsed']
                except KeyError:
                    when = e['updated_parsed']
                when = datetime(*when[:6])
                when = utc.localize(when)

                try:
                    title = e['title']
                except KeyError:
                    title = blog
                try:
                    author = " ({})".format(e['authors'][0]['name'])
                except KeyError:
                    author = ""
                try:
                    body = e['content'][0]['value']
                except KeyError:
                    body = e['summary']
                link = e['link']

                # Include only posts that are less than 3 days old. Add older posts
                # to the read database.
                if when > daysago:
                    posts.append((when, blog, title, link, body,
                                  "{:04d}".format(n), author, id))
                    n += 1
                else:
                    addItem(db, blog, id)
    except:
        pass

# Sort the posts in reverse chronological order.
posts.sort()
posts.reverse()
body = ""
the_day = ""
prev_day = ""
day_text = ""

for p in posts:
    q = [x for x in p[1:]]
    timestamp = p[0].astimezone(homeTZ)
    # the_date = timestamp.strftime('%b %d, %Y %I:%M %p')
    the_date = timestamp.strftime('%I:%M %p')
    the_day = timestamp.strftime('%B %d, %Y')
    if the_day == prev_day:
        day_text = ""
    else:
        day_text = '<div class="day">' + the_day + '</div>'
        prev_day = the_day
    the_site = clean_sitename(q[0])
    pre_news = q[3]
    soup = BeautifulSoup(pre_news, features="html.parser")
    the_news = soup.get_text()
    the_link = q[2]
    the_headline = clean_headline(q[1])
    text = day_text + '<button class="collapsible">' + the_headline + \
        ' - <span class="source">' + the_site + \
        '</span><br /><span class="time">' + the_date + \
        '</span></button><div class="content"><p>' + the_news + \
        '</p><a href="' + the_link + \
        '" target="_blank">Read More</a><br /><br /></div>'
    body = body + text

# Create an HTML list of the video feed
listTemplate = '''<div class="news-row">
                    <a class="title" href="{3}" target="_blank">{2}</a>
                    <img src="assets/img/paperclip.png" style="height: 10px;" />
                    <span class="source">{1}</span><br />
                    <div class="source">4 {4}</div>                    
                    <div class="source">5 {5}</div>          
                    <div class="source">6 {6}</div>                       
                    <div class="source">7 {7}</div>                    
                    <div class="source">8 {8}</div>          
                    <div class="source">9 {9}</div>      
                    <div class="source">7 {10}</div>                         
                  </div>'''
litems = []
video = ''
for p in videos:
    q = [x for x in p[1:]]
    temp = q[3]
    description = temp.replace('Like on Facebook: http://goo.gl/sBqGfi', '')
    linky = q[2]
    imagelink = 'https://i2.ytimg.com/vi/' + \
        linky.replace('https://www.youtube.com/watch?v=', '') + \
        '/hqdefault.jpg'
    fixedbody = description.replace(
        'Follow on Twitter: http://goo.gl/TsvaMs', '')
    text = '<div class="news-row"><a class="title" href="' + q[2] + '" target="_blank">' + q[1] + '</a>' + '<span class="source">' + q[0] + '</span>' + \
        '<div class="news">' + fixedbody + '</div>' + \
        '<br /></div>'
    video = video + text


# Print the HTMl.
print('''<!DOCTYPE html>
<html>

<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="assets/css/styles.css">
</head>

<body>
<div class="header">F1NEWS</div>
'''

+ body + 
'''
    <script>
        var coll = document.getElementsByClassName("collapsible");
        var i;

        for (i = 0; i < coll.length; i++) {
            coll[i].addEventListener("click", function () {
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.style.maxHeight) {
                    content.style.maxHeight = null;
                } else {
                    content.style.maxHeight = content.scrollHeight + "px";
                }
            });
        }
    </script>

</body>

</html>''')
