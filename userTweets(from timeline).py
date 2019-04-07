from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time, sys, datetime


# https://stackoverflow.com/questions/47249937/tweet-ids-with-selenium

# since: datetime object
# until : datetime object
# since : string
def getUrl(user, since, until):
    since = since.strftime('%Y-%m-%d')
    until = until.strftime('%Y-%m-%d')
    p1 = 'https://twitter.com/search?f=tweets&vertical=default&q=from%3A'
    p2 =  user + '%20since%3A' + since + '%20until%3A' + until + '&src=typd'
    return p1 + p2

# Store username, password, user to find tweets and output file
userlog = sys.argv[1]
password = sys.argv[2]
user = sys.argv[3]
filePath = sys.argv[4]

# Set Firefox headlessly to save resources
options = Options()
options.headless = False

# Open twitter
browser = webdriver.Firefox(options=options)
browser.get("https://twitter.com/")

# Log in
userElem = browser.find_element_by_name("session[username_or_email]")
userElem.send_keys(userlog)
passElem = browser.find_element_by_name("session[password]")
passElem.send_keys(password)
loginElem = browser.find_element_by_xpath("/html/body/div[1]/div/div[1]/div[1]/div[1]/form/input[1]")
loginElem.click()

# Got to Twitter Tweets and Replies user's page

browser.get("https://twitter.com/%s/with_replies" % (user))

# Get total number of tweets
countElem = browser.find_element_by_class_name("ProfileNav-value")
numTweets = int(countElem.get_attribute("data-count"))

# Get url to start
until = datetime.datetime.now()
oneYear = datetime.timedelta(days=1825)
since = until - oneYear
url = getUrl(user, since, until)
browser.get(url)

# Get all tweets links
tweetLinks = []
htmlElem = browser.find_element_by_tag_name('html')

while len(tweetLinks) < numTweets: # CUANDO SE ENCUENTRE EL BOTON DE VOLVER ARRIBA, AVANZAR EL MES. PARAR CUANDO SE TENGAN TODOS LOS TWEETS
    # Scroll down and update list
    # All tweet links contains "status", find them with a CSS selector
    tweetLinks = browser.find_elements_by_css_selector("a[href*='status']")
    print("Current tweets stored: " + str(len(tweetLinks)))
    # It's not necessary, but we can use time.sleep to save cpu cycles
    # while page is loading after scroll down
    htmlElem.send_keys(Keys.END)
    time.sleep(1)

# Write tweet links into an output file

with open(filePath, 'w') as file:
    # Last url is status.twitter.com, not needed
    topLimit = len(tweetLinks) - 1
    for i in range(0, topLimit):
        link = tweetLinks[i].get_attribute("href")
        file.write(link + "\n")

# Log out and close browser
userMenu = browser.find_element_by_xpath("//*[@id='user-dropdown-toggle']")
userMenu.click()
#Wait until log out button is loaded
logOutElem = WebDriverWait(browser, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='signout-button']")))
logOutElem.click()
browser.close()

print("Done. All user's tweets copied to the given file.")
