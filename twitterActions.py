from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
import time, sys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def login(browser, user, password):
    browser.get("https://twitter.com/")

    # Log in
    userElem = browser.find_element_by_name("session[username_or_email]")
    userElem.send_keys(user)
    passElem = browser.find_element_by_name("session[password]")
    passElem.send_keys(password)
    loginElem = browser.find_element_by_xpath("/html/body/div[1]/div/div[1]/div[1]/div[1]/form/input[1]")
    loginElem.click()


def logout(browser):
    time.sleep(3)
    browser.get("https://twitter.com/")
    time.sleep(3)
    userMenu = browser.find_element_by_xpath("//*[@id='user-dropdown-toggle']")
    userMenu.click()
    #Wait until log out button is loaded
    logOutElem = WebDriverWait(browser, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='signout-button']")))
    logOutElem.click()
    browser.close()


# Note: selenium.common.exceptions.StaleElementReferenceException
# may be raised if your timeline updates while uploading tweet (element is refreshed)
# Return true if successful, returns false otherwise
def uploadTweetImg(browser, text, imgPath):
    try:
        # Select tweet box and upload img button
        tweetBox = browser.find_element_by_id('tweet-box-home-timeline')
        imgButton = browser.find_element_by_css_selector('input.file-input')

        # Write text and upload pic
        tweetBox.send_keys(text)
        time.sleep(1)
        imgButton.send_keys(imgPath)

        # wait till image is uploaded until going forward
        time.sleep(5)
        browser.find_element_by_css_selector('button.tweet-action').click()
        time.sleep(5)
        # Load home page again to allow new uploadTweetImg callings
        browser.get("https://twitter.com")
        return True
    except Exception as e:
        #return e
        print("Exception raised while upload tweet:")
        print(e)
        return False

#If the user is being followed, it results in unfollow.
#If user does not exists, return false, the exception is caught
def followUser(browser, user):
    try:
        url = "http://twitter.com/" + user
        browser.get(url)
        followButton = browser.find_element_by_css_selector(".UserActions")
        time.sleep(2)
        followButton.click()
        time.sleep(2)
        browser.get(current)
        return True
    except Exception as e:
        return False

#If the user is not being followed, it resutl in follow
def unfollowUser(browser,user):
    followUser(browser,user)
