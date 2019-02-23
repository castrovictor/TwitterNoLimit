from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time, sys, datetime
import bs4, requests, re
import csv
import collections

import asyncio

# https://stackoverflow.com/questions/47249937/tweet-ids-with-selenium

# Regex for tweet date
tweetDateRegex = re.compile(r'''(
\s?                     # separator
(?P<hour>\d{1,2})       # hour
:                       # : symbol
(?P<minute>\d{1,2})     # minute
\s{1}                   # separator
-                       # - symbol
\s{1}                   # separator
(?P<day>\d{1,2})        # day
\s{1}                   # separator
(?P<month>\w{3,4})      # month
\.{1}                   # . symbol
\s{1}                   # separator
(?P<year>\d{4})         # year
\s?                     # separator
)''', re.VERBOSE)

def monthtoNumber(month):
    switcher = {
        "ene": 1,
        "feb": 2,
        "mar": 3,
        "abr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "ago": 8,
        "sept": 9,
        "oct": 10,
        "nov": 11,
        "dic": 12
    }
    return switcher.get(month)

# since: datetime object
# until : datetime object
# since : string
def getUrl(user, since, until):
    since = since.strftime('%Y-%m-%d')
    until = until.strftime('%Y-%m-%d')
    p1 = 'https://twitter.com/search?f=tweets&vertical=default&q=from%3A'
    p2 =  user + '%20since%3A' + since + '%20until%3A' + until + '&src=typd'
    return p1 + p2

# Return date's tweet given by url
def getTweetDate(urlTweet):
    res = requests.get(urlTweet)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, features = "html.parser")
    dateElem = soup.select(".client-and-actions")
    dateText = dateElem[0].span.text
    matchDate = re.match(tweetDateRegex, dateText)

    minute = int(matchDate.group("minute"))
    hour = int(matchDate.group("hour"))
    day = int(matchDate.group("day"))
    month = monthtoNumber(matchDate.group("month"))
    year = int(matchDate.group("year"))
    dt = datetime.datetime(year,month,day, hour, minute)
    return dt



# since: datetime object
# until : datetime object
# since : string
def getTweets(user, since, until):
    # Set Firefox headlessly to save resources
    options = Options()
    options.headless = False

    # Open browser
    browser = webdriver.Firefox(options=options)

    # Get url to start
    oneYear = datetime.timedelta(days=365)
    url = getUrl(user, since, until)
    browser.get(url)

    # Get all tweets links
    # Tweets found with selenium selector
    tweets = []
    # url's tweets stored
    tweetLinks = set()
    htmlElem = browser.find_element_by_tag_name('html')

    endStream = False
    lastRound = 0
    MAX_COUNTER = 4
    counter = 0

    lastIteration = False
    while not endStream or lastIteration:
        # You can get random exception using a proxy, no idea why
        try:
            # Scroll down and update list
            # All tweet links contains "status", find them with a CSS selector
            tweets = browser.find_elements_by_css_selector("a[href*='status']")

            print("Current tweets stored: " + str(len(tweets)))
            print("Total tweets found: " + str(len(tweets) + len(tweetLinks)))

            if(len(tweets) == 0):
                print("0 tweets found, continue? ")

            # It's not necessary, but we can use time.sleep to save cpu cycles
            # while page is loading after scroll down
            htmlElem.send_keys(Keys.END)
            time.sleep(1)

            #Check if number of tweets stored is the same as last iteration
            currentRound = len(tweets)
            if(currentRound == lastRound):
                counter += 1
            lastRound = currentRound

            # If MAX_COUNTER consecutive itetarions storing the same number of tweets,
            # store tweets and load new twitter search until last Tweet
            if(counter == MAX_COUNTER):
                counter = 0
                # Last element is status.twitter.com, pop it

                # If len(tweets) is 0, no tweets remaining, just finish without
                # saving tweets
                if(len(tweets) > 0):
                    tweets.pop()
                    lastTweetUrl = tweets[len(tweets)-1].get_attribute("href")

                    # Store tweet links in a set structure (to avoid possible repeated tweets)
                    topLimit = len(tweets)
                    print("Store in the set, len: " + str(topLimit))
                    urlPrefix = "https://twitter.com/%s/status/" % user
                    for i in range(0, topLimit):
                        link = tweets[i].get_attribute("href")
                        # If tweet does not belong to the user, skip
                        # That's because mentioned tweet by the user are stored
                        if(not link.startswith(urlPrefix)):
                            continue

                        tweetLinks.add(link)

                    # Load new tweet search to continue scrapping tweets
                    dateLastTweet = getTweetDate(lastTweetUrl)

                # Finish because dateLast tweets is since's date or no tweets remaining
                if ((dateLastTweet.date() == since.date()) or (len(tweets) == 0)):
                    endStream = True
                    # One more iteration needed to store since's date tweets
                    lastIteration = True

                # Last iteration finished, stop the loop
                if(lastIteration):
                        print("No more tweets found, finishing the search..")
                        break

                # +1 day to include all tweets of that date
                oneDay = datetime.timedelta(days=1)
                until = getTweetDate(lastTweetUrl) + oneDay
                newUrl = getUrl(user, since, dateLastTweet)

                browserLoaded = False
                attempts = 0
                MAX_ATTEMPTS = 10
                TIME_SLEEP = 120
                TIMEOUT = 30
                # After several experiments, sometimes you can get
                # a timeout with selenium, catch it
                while not browserLoaded:
                    attempts += 1
                    try:
                        browser.set_page_load_timeout(TIMEOUT)
                        browser.get(newUrl)
                        htmlElem = browser.find_element_by_tag_name('html')
                        browserLoaded = True
                    except TimeoutException as ex:
                        # Wait 2 minutes and try again.
                        time.sleep(TIME_SLEEP)
                        # If 5 times without success, stop trying it
                        if(attempts == MAX_ATTEMPTS):
                            break;

                # If true, the timeout as not solved. Stop main loop
                if not browserLoaded:
                    print("Timeout exception while loading page, no new tweets stored after that")
                    break;
        except Exception as e:
            print("Exception catched, saving tweets found...")
            break;


    print("Returning tweets..")
    # Close browser
    browser.close()
    print("(Function) Len of links: " + str(len(tweetLinks)))
    return tweetLinks

#+1 day to include today's tweets
until = datetime.datetime.now() + datetime.timedelta(days=1)
#oneYear = datetime.timedelta(days=3)
since = datetime.datetime(2012,10,18)
links = getTweets("imaxi98", since, until)
#getTweetDate("https://twitter.com/MiguelLentisco/status/817132635793264640")


print("Len of links: " + str(len(links)))
with open(sys.argv[1] + "_nosorted.txt", 'w') as file:
    for link in links:
        file.write(link + "\n")
"""

# Save links sorted by date into a OrderedDictionary
dictTweet = {}

for link in links:
    print("Saving " + link)
    tweetDate = getTweetDate(link)
    timestamp = tweetDate.timestamp()
    dictTweet[timestamp] = link


sortedDictTweet = collections.OrderedDict(sorted(dictTweet.items()), key=lambda t: t[0])


outputFile = open(sys.argv[1] + "_ordered.csv", 'w', newline='')
outputWriter = csv.writer(outputFile, delimiter = '\t')

for key, value in sortedDictTweet.items():
    print("Writing " + link)
    date = datetime.fromtimestamp(key)
    tweetDate = date.strftime('%d/%m/%Y')
    outputWriter.writerow([value, tweetDate])

"""

print("Done. All user's tweets copied to the given file.")
