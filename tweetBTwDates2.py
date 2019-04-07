from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time, sys, datetime
import bs4, requests, re
import csv
import multiprocessing
from sortedcontainers import SortedDict


# Regex for tweet date
tweetNewDateRegex = re.compile(r'''(
\s?                     # separator
(?P<hour>\d{1,2})       # hour
:                       # : symbol
(?P<minute>\d{1,2})     # minute
\s{1}                   # separator
(?P<meridiem>\D{2})     # AM or PM
\s{1}                   # separator
-                       # - symbol
\s{1}                   # separator
(?P<day>\d{1,2})        # day
\s{1}                   # separator
(?P<month>\w{3,4})      # month
\s{1}                   # separator
(?P<year>\d{4})         # year
\s?                     # separator
)''', re.VERBOSE)


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


def NewMonthtoNumber(month):
    switcher = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sept": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12
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
    try:
        res = requests.get(urlTweet)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, features = "html.parser")
        dateElem = soup.select(".client-and-actions")
        print("DateElem:")
        print(dateElem)
        dateText = dateElem[0].span.text
        matchDate = re.match(tweetDateRegex, dateText)

        newRegexUsed = False
        if (matchDate is None):
            print("Using new regex..")
            newRegexUsed = True
            matchDate = re.match(tweetNewDateRegex, dateText)

        minute = int(matchDate.group("minute"))
        hour = int(matchDate.group("hour"))
        day = int(matchDate.group("day"))
        year = int(matchDate.group("year"))

        if (newRegexUsed):
            print("Calculando nuevo mes...")
            month = NewMonthtoNumber(matchDate.group("month"))
            meridiem = str(matchDate.group("meridiem"))
            if (meridiem == 'PM'):
                print("Sumando 12...")
                hour += 12
        else:
            month = monthtoNumber(matchDate.group("month"))

        print("Year %d, month: %d, day: %d, hour: %d, minute: %d" % (year,month,day,hour,minute))
        dt = datetime.datetime(year,month,day, hour, minute)
        return dt
    except requests.exceptions.RequestException as e:
        print(e)
        dt = datetime.datetime(1970,1,1,1,0,0)
        return dt



# since: datetime object
# until : datetime object
# since : string
def InnerGetTweets(user, since, until, queue):
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

            """
            print("Current tweets stored: " + str(len(tweets)))
            print("Total tweets found: " + str(len(tweets) + len(tweetLinks)))
            """

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

            # Store tweets always
            if(len(tweets) > 0):
                tweets.pop()

            # Store tweet links in a set structure (to avoid possible repeated tweets)
            topLimit = len(tweets)
            urlPrefix = "https://twitter.com/%s/status/" % user
            for i in range(0, topLimit):
                link = tweets[i].get_attribute("href")
                # If tweet does not belong to the user, skip
                # That's because mentioned tweet by the user are stored
                if(not link.startswith(urlPrefix)):
                    continue

                tweetLinks.add(link)

            # If MAX_COUNTER consecutive itetarions storing the same number of tweets,
            # load new twitter search until last Tweet
            if(counter == MAX_COUNTER):
                counter = 0
                # Last element is status.twitter.com, pop it

                # If len(tweets) is 0, no tweets remaining, just finish without
                # saving tweets
                if(len(tweets) > 0):
                    lastTweetUrl = tweets[len(tweets)-1].get_attribute("href")

                    # Load new tweet search to continue scrapping tweets
                    dateLastTweet = getTweetDate(lastTweetUrl)

                # Finish because dateLast tweets is since's date or no tweets remaining
                if ((len(tweets) == 0) or (dateLastTweet.date() == since.date())):
                    endStream = True
                    # One more iteration needed to store since's date tweets
                    lastIteration = True

                # Last iteration finished, stop the loop
                if(lastIteration):
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
            print(e)
            break;


    # Close browser
    browser.close()
    queue.put(tweetLinks)

#timeStripe: int, represent days
#timeoutDay : int, seconds limit to wait to get tweets
def getTweets(user, since, until, timeStripe, timeoutDay):
    # +1 day to include tweets of until date
    until = until + datetime.timedelta(days=1)

    begin = int(since.timestamp() - 1)
    # +1 to include until date
    finish = int(until.timestamp() + 1)
    inc = timeStripe * 24 * 3600

    tweetLinks = set()
    for i in range(begin, finish+1, inc):
        since = datetime.datetime.fromtimestamp(i)
        until = datetime.datetime.fromtimestamp(i+inc)

        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=InnerGetTweets, args=(user, since, until ,queue,))
        p.start()

        timeout = int(timeoutDay * timeStripe)
        p.join(timeout)

        # If thread is active, kill it and break loop, if not, save tweets
        if p.is_alive():
            p.terminate()
            p.join()
            break
        else:
            auxSet = queue.get()
            for item in auxSet:
                tweetLinks.add(item)

    return tweetLinks


# Receive a txt with tweet links and generates a csv file with tweets and dates, sorted
def TxtToCSVSorted(txtfile, csvfile):
    # Store tweet links
    with open(txtfile, 'r') as file:
        tweets = file.readlines()

    # Get dates and save in an OrderedDict
    dictTweet = {}
    date_errors = 0
    for link in tweets:
        # Delete \n at the end of the line
        link = link[:-1]
        print("Getting " + link)
        tweetDate = getTweetDate(link)
        print("Date:")
        print(tweetDate)
        if(tweetDate == datetime.datetime(1970,1,1,1,0,0)):
            tweetDate += datetime.timedelta(days=date_errors)
            date_errors += 1

        timestamp = tweetDate.timestamp()
        dictTweet[timestamp] = link

    #sortedDictTweet = collections.OrderedDict(sorted(dictTweet.items()), key=lambda t: t[1])

    outputFile = open(csvfile, 'w', newline='')
    outputWriter = csv.writer(outputFile, delimiter = '\t')
    sortedDictTweet = SortedDict(dictTweet)

    for key,value in sortedDictTweet.items():
        print("Writing " + str(key) +"--" + str(value))
        date = datetime.datetime.fromtimestamp(key)
        tweetDate = date.strftime('%d/%m/%Y')
        outputWriter.writerow([value, tweetDate])




"""

#+1 day to include today's tweets
until = datetime.datetime.now() + datetime.timedelta(days=1)
#oneYear = datetime.timedelta(days=3)
since = datetime.datetime(2018,10,18)
links = getTweets("iMaxi98", since, until, 300, 60)
#getTweetDate("https://twitter.com/MiguelLentisco/status/817132635793264640")

print("Len of links: " + str(len(links)))
with open(sys.argv[1] + "_nosorted.txt", 'w') as file:
    for link in links:
        file.write(link + "\n")
        """

#TxtToCSVSorted("salidaPaisajes.txt_nosorted.txt", "paisajes_sorted.csv")

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

#print("Done. All user's tweets copied to the given file.")
