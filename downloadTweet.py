from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

import bs4, requests, re
import os, csv


#Return a tuple, whose first elemt is tweet's text and second one the url's picture
#Note: if no image is attached to the tweet, profile pic is returned
#Return an empty tuple if exception raised

def downloadTweet(url):
    res = requests.get(url)
    try:
        res.raise_for_status()
    except Exception as exc:
        print("Problem with current tweet")
        return ()

    soup = bs4.BeautifulSoup(res.text, features = "html.parser")

    textElem = soup.find("meta", property="og:description")
    picElem = soup.find("meta",  property="og:image")
    text = textElem.get("content")
    pic = picElem.get("content")

    return (text,pic)


# Receives a txt file and return a vector whose each component is a line
# of the file given
def TxtToVector(file):
    with open(file, 'r') as file:
        tweets = file.readlines()
        for i in range(len(tweets)):
            # Delete /n at the end of the line
            url = tweets[i]
            tweets[i] = url[:-1]

        return tweets

# Receives a vector where each component is a tweet url and download tweets
# path: where to store tweets
# If tweet does not contain picture, counts as fail
# If tweet contain twitter link, counts as fail
def tweetsDownload(tweets, path, csvfile):
    tweetFails = 0
    tweetSuccess = 0
    missingFlagS = "https://t.co/"
    missingFlag = " http://t.co/"

    # Creat folder to save pics
    picFolderPath = path + "/images"
    os.makedirs(picFolderPath, exist_ok=True)

    #Create csvFile
    outputFile = open(csvfile, 'w', newline='')
    outputWriter = csv.writer(outputFile, delimiter = '\t')

    totalTweets = str(len(tweets))
    iteration = 0
    for tweet in tweets:
        print("Current iteration " + str(iteration) + " of " + totalTweets)
        iteration += 1

        tuple = downloadTweet(tweet)

        if(len(tuple) == 0):
            print("Error with url %d" % (iteration))
            tweetFails += 1
            continue

        text = tuple[0]
        text = text[1:-1]
	    # Delete " at the beginning and at the end of the text
        if((text.find(missingFlagS) != -1) or (text.find(missingFlag) != -1)):
            tweetFails += 1
            continue
        else:
            tweetSuccess += 1

        picUrl = tuple[1]

        #Download pic and write it
        res = requests.get(picUrl)
        try:
            res.raise_for_status()
        except Exception as exc:
            print("Problem with current img, skipping..")
            tweetSuccess -= 1
            tweetFails += 1
            continue

        imgPath = picFolderPath + "/" + str(tweetSuccess)
        imageFile = open(imgPath, 'wb')
        for chunk in res.iter_content(100000):
            imageFile.write(chunk)
        imageFile.close()

        # Write info into csv
        outputWriter.writerow([text, imgPath])

    print("Success %d, fail %d" % (tweetSuccess,tweetFails))



tweets = TxtToVector("paisajes_nosorted.txt")
tweetsDownload(tweets, "./paisajes3", "./paisajes3/paisajes3.csv")
