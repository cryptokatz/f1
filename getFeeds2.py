import numpy
from operator import itemgetter
import math
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
import nltk
import operator
import math
from operator import itemgetter

def addItem(db, blog, id):
    add = 'insert into items (blog, id) values (?, ?)'
    db.execute(add, (blog, id))
    db.commit()


def freq(word, document):
    return document.count(word)


def wordCount(document):
    return len(document)


def numDocsContaining(word, documentList):
  count = 0
  for document in documentList:
    if freq(word, document) > 0:
      count += 1
  return count

def top_keywords(n, doc, corpus):
    d = {}
    for word in set(doc):
        d[word] = tfidf(word, doc, corpus)
    sorted_d = sorted(d.items(), key=operator.itemgetter(1))
    sorted_d.reverse()
    return [w[0] for w in sorted_d[:n]]

def tf(word, document):
    return (freq(word, document) / float(wordCount(document)))


def idf(word, documentList):
    return math.log(len(documentList) / numDocsContaining(word, documentList))


def tfidf(word, document, documentList):
    return (tf(word, document) * idf(word, documentList))

def clean_sitename(site_name):
    """This function returns the absolute
    value of the entered number"""

    s1 = site_name.replace("Formula 1 news - Autosport", "Autosport")
    s2 = s1.replace(" - the latest hottest F1 news", "")
    s3 = s2.replace("BBC Sport - Formula 1", "BBC Sport")
    s4 = s3.replace(" :: F1 Feed", "")
    s5 = s4.replace(" - Formula 1 - Stories", "")
    s6 = s5.replace("top scoring links : formula1", "r/formula1")
    return s6

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
    'https://www.racefans.net/feed/'
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
corpus = []
titles = []
ct = -1

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
                    title = clean_headline(e['title'])
                    words = nltk.wordpunct_tokenize(nltk.clean_html(e['description']))
                    wt = [1.0] * len(words)
                    title = nltk.wordpunct_tokenize(title)
                    words.extend(title)
                    wt.extend(3 * len(title))
                    lowerwords=[x.lower() for x in words if len(x) > 1]
                    ct += 1
                    print (ct,"TITLE",title)
                    corpus.append(lowerwords)
                    titles.append(title)
                    wts.append(wt)
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

key_word_list = set()
nkeywords = 6
[[key_word_list.add(x) for x in top_keywords(nkeywords, doc, corpus)]
 for doc in corpus]

ct = -1
for doc in corpus:
   ct += 1
   print (ct, "KEYWORDS", " ".join(top_keywords(nkeywords, doc, corpus)))

feature_vectors = []
n = len(corpus)

for document in corpus:
    vec = []
    [vec.append(tfidf(word, document, corpus) if word in document else 0)
     for word in key_word_list]
    feature_vectors.append(vec)

