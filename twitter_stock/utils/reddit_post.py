import praw
import os
from .analyze_tasks import Predict
from luigi import build

# establish API
reddit = praw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    user_agent="<console:twitter_stock:0.0.1 (by /u/test_acc_reddit>",
    username=os.environ["REDDIT_USERNAME"],
    password=os.environ["REDDIT_PASSWORD"],
)


def post(ticker, date):
    """
    Post prediction result to reddit
    """

    build([Predict(ticker=ticker, date=date)], local_scheduler=True)
    subreddit = reddit.subreddit("prediction")
    try:
        subreddit.submit(
            title="Stock Prediction by Twitter Sentiment",
            selftext=Predict(ticker=ticker, date=date).get_result(),
        )
        return True

    except praw.exceptions.RedditAPIException as e:
        print(e.message)
        return False
