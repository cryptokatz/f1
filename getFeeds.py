# coding: utf-8

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
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import ftfy

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
    s7 = s6.replace("F1 News, Reports and Race Results - F1i.com", "F1i")
    s8 = s7.replace("News - F1-Insider.com", "F1-Insider")
    s9 = s8.replace("F1Technical.net . Motorsport news", "F1Technical")
    s10 = s9.replace("www.espn.com - F1","ESPN")
    if s10.find("thejudge13") != -1:
        s10 = "thejudge13"
    if s10.find("EssentiallySports") != -1:
        s10 = "EssentiallySports"    
    text = ftfy.fix_text(s10)
    return text


def clean_headline(headline):
    sep = '|'
    rest = headline.split(sep, 1)[0]
    text = ftfy.fix_text(rest)
    return text

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
    'https://www.autosport.com/rss/feed/f1',
    'https://www.motorsport.com/rss/f1/news/',
    'https://www.reddit.com/r/formula1/top.rss?t=day&limit=5',
    'http://futureneteam.biz/category/formula-1/feed/',
    'https://en.f1i.com/news/feed',
    'https://www.f1technical.net/rss/news.xml',
    'https://www.essentiallysports.com/category/f1/feed/',
    'https://www.espn.com/espn/rss/f1/news'
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
        clean_text = ftfy.fix_text(e['description'])
        words = nltk.wordpunct_tokenize(clean_text)
        words.extend(nltk.wordpunct_tokenize(clean_title))

        stop_words = set(stopwords.words('english'))

        lowerwords = [x.lower() for x in words if len(x) > 1]

        filtered = []
        important = ['chassis','fernando','alonso','alpha','alphatauri','brown','f1','leclerc','mclaren','fp1','fp2','valterri', 'pole', 'live', 'qualifying', 'renault', 'ricciardo', 'ocon', 'mclaren', 'norris', 'sainz', 'hulkenberg', 'announce', 'contract', 'concorde', 'bottas', 'mercedes', 'lewis',
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
        titles.append(clean_title)

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


key_word_list = set()
nkeywords = 5
[[key_word_list.add(x) for x in top_keywords(nkeywords, doc, corpus)]
 for doc in corpus]
for doc in corpus:
   ct += 1

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
        mat[i][j] = nltk.cluster.util.cosine_distance(
            feature_vectors[i], feature_vectors[j])


t = 0.80
Z = linkage(mat, 'complete')

clusters = extract_clusters(Z, t, n)

print('''<!DOCTYPE html>
<html>

<head>
<title>GPWEEKEND - Formula 1 News Aggregator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="assets/css/styles.css">
    <link href="https://fonts.googleapis.com/css2?family=Raleway&display=swap" rel="stylesheet">
</head>

<body>
    
    <div class="row">
    <div class="header"><div class='logo'><img src='logo.png'></div></div>
    <div class="column left">    
''')

posts = []

for key in clusters:
    first = 1
    code = " " + "<div class='item'>"
    for id in clusters[key]:
        ## The first article in the cluster
        if first == 1:
            # Extract the first sentence from each sentence
            # so we can avoid the last sentences from each site like social media promotion
            cleaned = text[id].partition('.')[0] + '.'
            code += "<div class='sitename'>" + "<a href='" + \
                sitelink[id] + "'>" + publisher[id] + "</a></div>"
            code += "<div class='headline'>" + "<a href='" + \
                link[id] + "'>" + titles[id] + "</a></div>"
            code += "<div class='text'>" + cleaned + "</div>"
            first = first + 1
            code += "<div class='more'>More: "
            the_date = date[id]
        # All other articles in the cluster go to the secondary linsk
        else:
            code += "<a href=" + \
                link[id] + ">" + "[" + publisher[id] + "] " + \
                    titles[id] + "</a><br/> "
        top_story[id] = "yes"
    code += "</div></div>"
    posts.append((the_date, code))

posts.sort()
posts.reverse()

for p in posts:
    print(p[1])

print("</div><div class='column middle'>")

latest = []
num = len(titles)
for i in range(0, num):
    code = ""
    if top_story[i] == "no":
        code += "<div class='item2'><div class='sitename'>" + \
            "<a href='" + sitelink[i] + "'>" + publisher[i] + "</a></div>"
        code += "<div class='headline2'>" + "<a href='" + \
            link[i] + "'>" + clean_headline(titles[i]) + "</a></div></div>"
        latest.append((date[i], code))

latest.sort()
latest.reverse()

count = 1
for l in latest:
    if count < 20:
        print(l[1])
    count += 1

print(
    '''
</div>
</div>

</body >

</html >''')
