import sys
sys.stderr = sys.stdout
import urllib, urllib2, json, MySQLdb
from dateutil.relativedelta import relativedelta
from BeautifulSoup import BeautifulSoup
import cgi, cgitb
cgitb.enable()
form = cgi.FieldStorage()

print 'Content-Type: text/plain; charset="UTF-8"'
print

courseids = form.getvalue("courseids")
user = form.getvalue("user")
language = form.getvalue("language")

start = form.getvalue("start")
end = form.getvalue("end")

if not language:
    language = "en"

if user:
    # If there are non-ascii characters, we need to convert them back from url encoding
    user = BeautifulSoup(user, convertEntities=BeautifulSoup.HTML_ENTITIES)
    user_list = '"' + str(user) + '"'

if not start:
    start = "200101"
    end = "202001"

## test course ids
# courseids = "6|72|35|4|77|60|34|97|66"

if courseids:
    api_query_url = "http://" + language + ".wikipedia.org/w/api.php?action=liststudents&format=json&courseids=" + courseids
    response = urllib2.urlopen(api_query_url)
    str_response = response.read()
    data = json.loads(str_response, "utf8" )
    users_data = data["students"]
    users = []
    for user in users_data:
        users.append(user["username"])
    user_list = '"' + '","'.join(users) + '"'
    # re-encode so that we can make a usable sql query string
    user_list = user_list.encode("utf8")
    # print user_list

sql_query = 'SELECT page_title FROM page WHERE page_id IN (SELECT DISTINCT rev_page FROM revision_userindex WHERE rev_user_text IN (' + user_list + ') AND rev_timestamp BETWEEN "' + start + '" and "' + end + '") AND page_namespace = 0 AND NOT page_is_redirect'

f = open("/data/project/coursestats/dbpassword", 'r')
dbpassword = f.read().rstrip()
f.close()

db = MySQLdb.connect( language + "wiki.labsdb","s52158",dbpassword, language + "wiki_p")
cursor = db.cursor()
cursor.execute(sql_query)
articles_edited = cursor.fetchall()

# remove the "page_title" line at the start of the sql output
# articles_edited = articles_edited[11:]

#print sql_query
for row in articles_edited:
    print row[0]
