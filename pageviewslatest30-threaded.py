#!/usr/bin/python3
 
import urllib, urllib.parse, urllib.request, json, csv, sys, datetime, os
from dateutil.relativedelta import relativedelta
from queue import Queue
from threading import Thread

# first command line argument is an existing file of article titles, one per line
articles = sys.argv[1]
# second command line argument is the name of the file where you want results to be compiled, in csv format
outputfile = sys.argv[2]

baseurl = 'http://stats.grok.se/json/en/latest30/'

# get page views for a single article for the last 30 days
def articleviews(article):
    articleurl = baseurl + urllib.parse.quote(article)

    # Try to get the data via url request, and retry if it fails
    attempts = 0
    while attempts < 10:
        try:
            response = urllib.request.urlopen(articleurl)
            attempts = 100
        except urllib.error.HTTPError as e:
            print("HTTP Error:",e.code , articleurl)
            attempts += 1
    # Stop the program if more than 10 attempts fail.
    if attempts == 10:
        print('Too many tries on ' + articleurl )
        raise 

    str_response = response.readall().decode('utf-8')
    data = json.loads(str_response)

    article_name = data['title']

    views= data['daily_views']

    view_sum = sum(views.values())

    f = open(outputfile,'a')
    w = csv.writer(f, delimiter=',')
    for day in views:
        w.writerow([ article, day, views[day] ])
        print ([ article, day, views[day] ])

def doWork():
    while True:
        item = q.get()
        article = item[0]
        articleviews( article )
        q.task_done()

# open the articles file, count the lines
num_articles = sum(1 for line in open(articles))
f = open(articles, 'r')

# start the output file with the column names.
ff = open(outputfile,'a')
w = csv.writer(ff, delimiter=',')
w.writerow(["article", "date", "pageviews"])
ff.close()

# create a queue
concurrent = 50
q = Queue(concurrent*2)
for i in range(concurrent):
    t=Thread(target=doWork)
    t.daemon=True
    t.start()

# collect the data
i = 0
for line in f:
    article = line.rstrip()
    i += 1
    print( "fetching views for article " + str(i) + " / " + str(num_articles))
    q.put( [ article ] )
q.join()

print ( "done fetching page view data." )


