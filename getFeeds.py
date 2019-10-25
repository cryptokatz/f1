import feedparser as fp
import time
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import sys
import dateutil.parser as dp
import urllib2
import json
import sqlite3
import urllib

def addItem(db, blog, id):
  add = 'insert into items (blog, id) values (?, ?)'
  db.execute(add, (blog, id))
  db.commit()

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
  'https://www.pitpass.com/fes_php/fes_usr_sit_newsfeed.php?fes_prepend_aty_sht_name=1',
  'https://peterwindsor.com/feed/'
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
        when =  datetime(*when[:6])
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
          posts.append((when, blog, title, link, body, "{:04d}".format(n), author, id))
          n += 1
        else:
          addItem(db, blog, id)
  except:
    pass

# PODCAST FEEDS
for s in podcastsubscriptions:
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
      match = db2.execute(query, (blog, id)).fetchone()
      if not match:
    
        try:
          when = e['published_parsed']
        except KeyError:
          when = e['updated_parsed']
        when =  datetime(*when[:6])
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
        
        # Include only posts that are less than 7 days old. Add older posts
        # to the read database.
        if when > weekago:
          podcasts.append((when, blog, title, link, body, "{:04d}".format(n2), author, id))
          n2 += 1
        else:
          addItem(db2, blog, id)
  except:
    pass


# VIDEO FEEDS
for s in videosubscriptions:
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
      match = db3.execute(query, (blog, id)).fetchone()
      if not match:
    
        try:
          when = e['published_parsed']
        except KeyError:
          when = e['updated_parsed']
        when =  datetime(*when[:6])
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
        
        # Include only posts that are less than 7 days old. Add older posts
        # to the read database.
        if when > weekago:
          videos.append((when, blog, title, link, body, "{:04d}".format(n3), author, id))
          n3 += 1
        else:
          addItem(db3, blog, id)
  except:
    pass

# Sort the posts in reverse chronological order.
posts.sort()
posts.reverse()
podcasts.sort()
podcasts.reverse()
videos.sort()
videos.reverse()



# Create an HTML list of the news feed
listTemplate = '''<div class="news-row">
                    <a class="title" href="{3}" target="_blank">{2}</a>
                    <img src="assets/img/paperclip.png" style="height: 10px;" />
                    <span class="source">{1}</span><br />
                    <div class="news">{4}</div>
                    <div class="source">{0}</div>                    
                  </div>'''
litems = []
for p in posts:
  q = [ x.encode('utf8') for x in p[1:] ]
  timestamp = p[0].astimezone(homeTZ)
  q.insert(0, timestamp.strftime('%b %d, %Y %I:%M %p'))
  q += [urllib.quote_plus(q[1]),
        urllib.quote_plus(q[7]),
        urllib.quote_plus(q[2]),
        urllib.quote_plus(q[3])]
  litems.append(listTemplate.format(*q))
body = ''.join(litems)



# Create an HTML list of the podcast feed
listTemplate = '''<div class="news-row">
                    <a class="title" href="{3}" target="_blank">{2}</a>
                    <img src="assets/img/paperclip.png" style="height: 10px;" />
                    <span class="source">{1}</span><br />
                    <div class="news">{4:.60}</div>
                    <div class="source">{0}</div>                    
                  </div>'''
litems = []
for p in podcasts:
  q = [ x.encode('utf8') for x in p[1:] ]
  timestamp = p[0].astimezone(homeTZ)
  q.insert(0, timestamp.strftime('%b %d, %Y %I:%M %p'))
  q += [urllib.quote_plus(q[1]),
        urllib.quote_plus(q[7]),
        urllib.quote_plus(q[2]),
        urllib.quote_plus(q[3])]
  litems.append(listTemplate.format(*q))
  podcast = ''.join(litems)



# Create an HTML list of the podcast feed
listTemplate = '''<div class="news-row">
                    <a class="title" href="{3}" target="_blank">{2}</a>
                    <img src="assets/img/paperclip.png" style="height: 10px;" />
                    <span class="source">{1}</span><br />
                    <div class="news">{4:.120}</div>
                    <div class="source">{0}</div>                    
                  </div>'''
litems = []
for p in videos:
  q = [ x.encode('utf8') for x in p[1:] ]
  timestamp = p[0].astimezone(homeTZ)
  q.insert(0, timestamp.strftime('%b %d, %Y %I:%M %p'))
  q += [urllib.quote_plus(q[1]),
        urllib.quote_plus(q[7]),
        urllib.quote_plus(q[2]),
        urllib.quote_plus(q[3])]
  litems.append(listTemplate.format(*q))
  video = ''.join(litems)


# Print the HTMl.
print '''<html>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width" />
<head>
		<meta charset="utf-8">
		<title>F1 News</title>
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<meta name="Description" lang="en" content="formula 1 news, videos, podcasts, and analysis from around the web">
		<meta name="author" content="kahthan deane">
		<meta name="robots" content="index, follow">

		<!-- icons -->
		<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
		<link rel="shortcut icon" href="favicon.ico">

		<!-- Override CSS file - add your own CSS rules -->
		<link rel="stylesheet" href="assets/css/styles.css">
	</head>

<html lang="en">

	<body>
		<div class="header">
			<div class="container">
			</div>
		</div>
		<div class="content">
			<div class="container">
				<div class="col1">
  
  <h1 class="header-heading">LATEST NEWS</h1>
  {}
  
				</div>
				<div class="col2">
							<h1 class="header-heading">PODCASTS</h1>
{}
              <h1 class="header-heading">VIDEOS</h1>
{}
				</div>
			</div>
		</div>
		<div class="footer">
			<div class="container">
				&copy; Copyright 2018
			</div>
		</div>
	</body>
</html>

'''.format(body,podcast,video)
