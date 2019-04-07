import datetime
import csv
import sys
#My own functions
import mydata
import storeData
from twitterActions import *

MY_SCREEN_NAME = 'victorcastro_98'
MY_PASSWORD = open("./mypassword.txt").read().strip()
MY_PYFILE = "./mydata.py"


# Set Firefox headlessly to save resources
options = Options()
options.headless = False
browser = webdriver.Firefox(options=options)

login(browser, MY_SCREEN_NAME, MY_PASSWORD)


# Script will be lauch at 15:00 by the cron daemon
#Script will work until ~03:00 AM of the following day (12 hours more or less in total)
init = datetime.datetime.now()
#twelveHours = datetime.timedelta(hours=12)
fourHours = datetime.timedelta(hours=4)
until = init + fourHours


dataFile = open('./paisajes3.csv')
dataReader = csv.reader(dataFile, delimiter='\t')
dataList = list(dataReader)


path = "/mnt/HDD 1TB/Documentos ASUS/Recursos Python/Twitter Scripts/"

# Load status information from last execution
userStack = mydata.list
#First tweet of the csv file that will be uploaded
positionData = sys.argv[1]

for i in range(0,3):
    print("Uploading tweet, positionData is " + positionData)
    # Load tweet
    text = dataList[positionData][0]
    imgPath = path + dataList[positionData][1] + ".jpg"
    positionData += 1

    # Upload tweet
    success = False
    while not success:
        success = uploadTweetImg(browser, text, imgPath)
        time.sleep(10)

    while init < until:
        user = userStack.pop()
        followUser(browser,user)
        time.sleep(300)
        user = userStack.pop()
        #Now follow user, in the future, handle another list to unfollow users simultaneously
        followUser(browser,user)
        time.sleep(300)

    init = until
    until = init + fourHours

#Save information about execution status
storeData.usersToFile(userStack, MY_PYFILE, "list")


logout(browser)
time.sleep(5)
browser.close()
