import sys
sys.stderr = sys.stdout
print 'Content-Type: text/plain; charset="UTF-8"'
print
print 'article, month, pageviews'
import urllib, urllib2, json, csv, sys, datetime, os
from dateutil.relativedelta import relativedelta
from BeautifulSoup import BeautifulSoup
from threading import Thread
import threading
from Queue import Queue

import cgi, cgitb
cgitb.enable()
form = cgi.FieldStorage()

## first command line argument is an existing file of article titles, one per line
article = form.getvalue("article")
courseid = form.getvalue("courseid")
language = form.getvalue("language")

if not language:
    language = "en"

baseurl = 'http://stats.grok.se/json/' + language + '/'

# default for command line testing
if not (courseid or article):
    courseid = "66"

if courseid:
    api_query_url = "http://" + language + ".wikipedia.org/w/api.php?action=liststudents&csv&format=json&courseids=" + courseid
    response = urllib2.urlopen(api_query_url)
    str_response = response.read()
    data = json.loads(str_response,"utf8")
    articles = data["0"]
    articles = [s.strip().encode("utf8") for s in articles.splitlines()]
    # the first line from the api is blank, so start from the second
    articles = articles[1:]
    # print articles

if article:
    article = BeautifulSoup(article, convertEntities=BeautifulSoup.HTML_ENTITIES)
    articles = [ str(article) ]
    # print articles

try:
    start_year = int(form.getvalue("startyear"))
    start_month = int(form.getvalue("startmonth"))
    end_year = int(form.getvalue("endyear"))
    end_month = int(form.getvalue("endmonth"))
except:
    start_year = 2014
    start_month = 6
    end_year = 2014
    end_month = 6

# start from the beginning of 2010
start_date = datetime.date( start_year, start_month, 1)
# go all the way to the current month
# end_date = datetime.date.today()
end_date = datetime.date( end_year, end_month, 1)

d = start_date
dates = []
delta = relativedelta( months = +1 )

while d <= end_date:
    month = d.strftime("%Y") + d.strftime("%m")
    dates.append( month )
    d += delta

# get page views for a single article for a single month
def articleviews(article, month):
    articleurl = baseurl + month + '/' + urllib.quote(article)
    # Try to get the data via url request, and retry if it fails
    attempts = 0
    while attempts < 10:
        try:
            response = urllib2.urlopen(articleurl)
            attempts = 100
        except: # urllib2.HTTPError as e:
            print("HTTP Error:",e.code , articleurl)
            attempts += 1
    # Stop the thread if more than 10 attempts fail.
    if attempts == 10:
        print('Too many tries on ' + articleurl )
        raise

    str_response = response.read()
    data = json.loads(str_response)

    article_name = data['title']

    views= data['daily_views']

    view_sum = sum(views.values())
    datapoint = article + "," + month + "," + str(view_sum)
    print datapoint

# fetch the arguments for one request and initiate the request
def viewsthread():
    x = True
    while x:
        task = q.get()
        article = task[0]
        month = task[1]
        articleviews( article, month )
        q.task_done()
        if q.empty():
            x = False

# count how many total requests, so we don't start too many threads
total_requests = 0
for art in articles:
    for month in dates:
        total_requests += 1

# create a queue for multi-thread requests
concurrent = 10 # not too high, or the webserver gets killed
if total_requests < concurrent:
    concurrent = total_requests

q = Queue()
for i in range(concurrent):
    t = Thread(target=viewsthread)
    t.Daemon = True
    t.start()

# populate the queue
for art in articles:
    for month in dates:
        q.put( [ art, month ] )

q.join()
