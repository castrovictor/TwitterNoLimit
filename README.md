## Set of Twitter Scripts to follow users, upload tweets, download tweets and more, using Python3, selenium and beautifoulsoup4.
Twitter's API is nos usted in order to avoid its restrictions. For example, with the API you can only download lastest 3200 tweets from a user's profile,
while with my script I have been able to download all the ~11k tweets of a user's profile.

### Project status
This repository is under development. I will try to improve it, but I have very little free time due to my university studies.

### Project scope
+ Learn Python, web scraping and web automation
+ Try to create Twitter accounts working as normal users, getting followers (trying followback technique), completely automatic.

### Important
While I was working in this project, a new version of Twitter interface appeared. Possibly, minor modifications will be necessary to work with it.
Nevertheless, this new version has to be selected manually.

### Pending
  + Documentation
  + Revise all functions
  + Include little modifications to current functions in order to have more flexibility: for example, in download Tweets(from timeline or the improved version using twitter advanced search,
  include or not include RT's, avoid tweets with/without pics...)
  + Do more functions (give like to a tweet, retweet...)
  + Adapt it to the new twitter interface
  

### Note
Exceptions are caught as Exception class, according to Python Exception Hierarchy. Differents exceptions can be trown depending on your internet connection
and previous executions. I mean, despite the fact that We are not using the API, after a lot of request (for example, downloading 50k tweets), Twitter may block
your search in different ways. Handling all different kinds of exceptions not worth it, as it would complicate the code more than it's necessary.

