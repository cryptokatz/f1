from hcluster import linkage
import numpy
import feedparser
import nltk
import math
from operator import itemgetter
import operator


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
    """This function returns the absolute
    value of the entered number"""

    s1 = site_name.replace("Formula 1 news - Autosport", "Autosport")
    s2 = s1.replace(" - the latest hottest F1 news", "")
    s3 = s2.replace("BBC Sport - Formula 1", "BBC Sport")
    s4 = s3.replace(" :: F1 Feed", "")
    s5 = s4.replace(" - Formula 1 - Stories", "")
    s6 = s5.replace("top scoring links : formula1", "r/formula1")
    if s6.find("thejudge13") != -1:
        s6 = "thejudge13"
    return s6


def clean_headline(headline):
    sep = '|'
    rest = headline.split(sep, 1)[0]
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
    'https://racingnews.co/tag/formula-one/feed/',
    'https://www.grandprix247.com/feed/',
    'http://feeds.feedburner.com/daily-express-f1',
    'https://www.planetf1.com/feed/',
    'https://www.pitpass.com/fes_php/fes_usr_sit_newsfeed.php?fes_prepend_aty_sht_name=1',
    'https://peterwindsor.com/feed/',
    'https://www.autosport.com/rss/feed/f1',
    'https://www.motorsport.com/rss/f1/news/',
    'https://www.reddit.com/r/formula1/top.rss?t=day&limit=5'
    ]

corpus = []
titles = []
publisher = []
text = []
authors = []


ct = -1
for feed in feeds:
    d = feedparser.parse(feed)
    for e in d['entries']:
        words = nltk.wordpunct_tokenize(e['title'])
        lowerwords = [x.lower() for x in words if len(x) > 1]
        ct += 1
        corpus.append(lowerwords)
        titles.append(clean_headline(e['title']))
        text.append(e['description'])
        publisher.append(clean_sitename(d['feed']['title']))


key_word_list = set()
nkeywords = 8
[[key_word_list.add(x) for x in top_keywords(nkeywords, doc, corpus)]
 for doc in corpus]

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


t = 0.8
Z = linkage(mat, 'single')


clusters = extract_clusters(Z, t, n)

first = 0

for key in clusters:
    first = 1
    print(" ")
    print("<div class='item'>")
    for id in clusters[key]:
        if first == 1:
            print("<div class='sitename'>",publisher[id],"<div>") 
            print("<div class='headline'>", titles[id], "<div>")
            print("<div class='content'>",text[id], "<div>")
            first = first + 1
            print("More: ", end='')
        else:
            print(publisher[id], " ", end='')
    print("</div>")
