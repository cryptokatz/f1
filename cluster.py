from hcluster import linkage
import numpy
import feedparser
import nltk
import math
import pytz
from operator import itemgetter
import operator
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import dateutil.parser as dp
from nltk.stem import PorterStemmer 
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

utc = pytz.utc
homeTZ = pytz.timezone('US/Central')
daysago = datetime.today() - timedelta(days=2)
daysago = utc.localize(daysago)
weekago = datetime.today() - timedelta(days=7)
weekago = utc.localize(weekago)


def top_keywords(n, doc, corpus):
    d = {}
    for word in set(doc):
        d[word] = tfidf(word, doc, corpus)
    sorted_d = sorted(d.items(), key=operator.itemgetter(1))
    sorted_d.reverse()
    return [w[0] for w in sorted_d[:n]]


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


def tf(word, document):
    return (freq(word, document) / float(wordCount(document)))


def idf(word, documentList):
    return math.log(len(documentList) / numDocsContaining(word, documentList))


def tfidf(word, document, documentList):
    return (tf(word, document)*idf(word, documentList))


def clean_sitename(site_name):
    s1 = site_name.replace("Formula 1 news - Autosport", "Autosport")
    s2 = s1.replace(" - the latest hottest F1 news", "")
    s3 = s2.replace("BBC Sport - Formula 1", "BBC Sport")
    s4 = s3.replace(" :: F1 Feed", "")
    s5 = s4.replace(" - Formula 1 - Stories", "")
    s6 = s5.replace("top scoring links : formula1", "r/formula1")
    if s6.find("thejudge13") != -1:
        s6 = "thejudge13"
    rest = s6.replace("`", "'")
    rest = rest.replace("’", "'")
    rest = rest.replace("‘", "'")
    return rest

def clean_headline(headline):
    sep = '|'
    rest = headline.split(sep, 1)[0]
    rest = rest.replace("`", "'")
    rest = rest.replace("’", "'")
    return rest


def extract_clusters(Z, threshold, n):
    clusters = {}
    ct = n
    for row in Z:
        if row[2] < threshold:
            n1 = int(row[0])
            n2 = int(row[1])
            if n1 >= n:
                l1 = clusters[n1]
                del(clusters[n1])
            else:
                l1 = [n1]

            if n2 >= n:
                l2 = clusters[n2]
                del(clusters[n2])
            else:
                l2 = [n2]
            l1.extend(l2)
            clusters[ct] = l1
            ct += 1
        else:
            return clusters


feeds = [
    'https://thejudge13.com/feed/',
    'http://feeds.bbci.co.uk/sport/formula1/rss.xml?edition=uk',
    'https://www.racefans.net/feed/',
    'https://www.jamesallenonf1.com/feed/',
    'https://www.grandprix247.com/feed/',
    'http://feeds.feedburner.com/daily-express-f1',
    'https://www.planetf1.com/feed/',
    'https://www.pitpass.com/fes_php/fes_usr_sit_newsfeed.php?fes_prepend_aty_sht_name=1',
    'https://peterwindsor.com/feed/',
    'https://f1-insider.com/category/news/feed/',
    'https://www.autosport.com/rss/feed/f1',
    'https://www.motorsport.com/rss/f1/news/',
    'https://www.reddit.com/r/formula1/top.rss?t=day&limit=5'
    ]

corpus = []
titles = []
publisher = []
text = []
authors = []
sitelink = []
link = []
date = []
top_story = []

ps = PorterStemmer()

ct = -1
for feed in feeds:
    d = feedparser.parse(feed)
    for e in d['entries']:
        clean_title = clean_headline(e['title'])
        words = nltk.wordpunct_tokenize((e['description']))
        words.extend(nltk.wordpunct_tokenize(e['title']))

        stop_words = set(stopwords.words('english'))

        lowerwords = [x.lower() for x in words if len(x) > 1]

        filtered = []
        important = ['valterri', 'pole', 'live', 'qualifying', 'renault', 'ricciardo', 'ocon', 'mclaren', 'norris', 'sainz', 'hulkenberg', 'announce', 'contract', 'concorde', 'bottas', 'mercedes', 'lewis',
                     'hamilton', 'ferrari', 'verstappen', 'red', 'bull', 'formula', '2021', 'sign', 'deal', 'vettel', 'perez', 'racing', 'point', 'stroll', 'horner', 'wolff', 'marko', 'leclerc', 'penalty', 'appeal']

        for w in lowerwords:
            if w not in stop_words:
                if len(w) > 1:
                    filtered.append(w)
            if w in important:
                filtered.append(w)    
                filtered.append(w)

        # Stem the words so we compare canonical words
        # lowerwords = [ps.stem(x) for x in words if len(x) > 1]
        
        corpus.append(filtered)

        # Clean the headline
        titles.append(clean_headline(e['title']))

        # Clean out the HTML from the article snippet
        soup = BeautifulSoup(e['description'], features="html.parser")
        news = soup.get_text()
        text.append(news)

        publisher.append(clean_sitename(d['feed']['title']))
        link.append(e['link'])
        sitelink.append(d['feed']['link'])
        top_story.append("no")

        # Get the localized dates
        try:
            when = e['published_parsed']
        except KeyError:
            when = e['updated_parsed']
        when = datetime(*when[:6])
        when = utc.localize(when)
        date.append(when)

ct = -1
key_word_list = set()
keywords = []
nkeywords = 5
[[key_word_list.add(x) for x in top_keywords(nkeywords, doc, corpus)] for doc in corpus]
for doc in corpus:
   ct += 1
   boom = " ".join(top_keywords(nkeywords, doc, corpus))
   keywords.append(boom)

feature_vectors = []
n = len(corpus)

for document in corpus:
    vec = []
    [vec.append(tfidf(word, document, corpus) if word in document else 0)
     for word in key_word_list]
    feature_vectors.append(vec)

mat = numpy.empty((n, n))
for i in range(0, n):
    for j in range(0, n):
        mat[i][j] = nltk.cluster.util.cosine_distance(feature_vectors[i], feature_vectors[j])

t = 0.8
Z = linkage(mat,'complete')

posts = []
clusters = extract_clusters(Z, t, n)
ct = -1
for key in clusters:
    print("-------------------------------")
    for id in clusters[key]:
        ct += 1
        print(ct, titles[id])
        print(ct, " - ",keywords[id])
