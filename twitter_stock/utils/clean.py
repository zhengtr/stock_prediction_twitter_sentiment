import dask
import math
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@dask.delayed
def clean_finance(file):
    """
    Helper function to clean data using dask
    """
    # read only columns needed
    finance = pd.read_parquet(file, columns=["Date", "Adj Close"])
    # fill the missing dates (market closed dates)
    alldate = pd.date_range(start=finance["Date"].min(), end=finance["Date"].max())
    finance = (
        finance.set_index("Date").reindex(alldate).rename_axis("Date").reset_index()
    )
    # fill in missing values
    finance["Adj Close"] = finance["Adj Close"].interpolate()
    finance["pct_change"] = finance["Adj Close"].pct_change()
    finance.drop("Adj Close", axis=1, inplace=True)
    return finance


@dask.delayed
def clean_twitter(file):
    """
    Helper function to clean data using dask
    """
    twitter = pd.read_parquet(file, columns=["Date", "Tweet content", "Followers"])
    # extract data for dates we need to align with all stock tickers
    twitter = twitter[
        (twitter["Date"] >= "2016-03-31") & (twitter["Date"] <= "2016-06-15")
    ]
    twitter = twitter[twitter["Followers"].notnull()]
    # get sentiment analysis of twitter content
    analyzer = SentimentIntensityAnalyzer()
    twitter["compound"] = twitter["Tweet content"].apply(
        lambda x: analyzer.polarity_scores(x)["compound"]
    )
    # take out "no sentiment" tweets
    twitter = twitter[twitter["compound"] != 0]
    # transform on followers (too much variance)
    twitter["Followers"] = twitter["Followers"].apply(math.log10)
    twitter["sentiment"] = twitter["Followers"] * twitter["compound"]
    out = twitter.groupby("Date")["sentiment"].mean().to_frame().reset_index()
    return out


@dask.delayed
def twitter_finance(file1, file2):
    """
    Helper function to combine data using dask
    """
    finance = list(dask.compute(clean_finance(file1)))[0]
    twitter = list(dask.compute(clean_twitter(file2)))[0]
    # combine data
    out = twitter.merge(
        finance, how="outer", right_on="Date", left_on="Date", sort=True
    )
    # fill in missing values where no data exists
    out["sentiment"][:-1].fillna(method="ffill", inplace=True)
    out["sentiment"][:-1].fillna(method="bfill", inplace=True)
    # get real buy/sell signal in order to train model
    out["signal"] = [True if x > 0 else False for x in out["pct_change"]]
    return out
