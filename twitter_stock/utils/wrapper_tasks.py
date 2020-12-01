from .analyze_tasks import *
from luigi import WrapperTask

# get all cashtags in order to use for all data
allcashtags = LocalCashtags().get_cashtags()


class LoadAllData(WrapperTask):
    """
    Wrapper task for loading several or all stock data together
    example usage: LoadAllData(['aapl', 'goog', 'fb'])  #specific stock tickers
                   LoadAllData('all')  #load all data
    """

    tickers = Parameter(default="all")

    def __init__(self, *args, **kwargs):
        # override to include parameter
        super().__init__(*args, **kwargs)

    def requires(self):
        tickers = allcashtags if self.tickers == "all" else self.tickers
        return [ExtracttoDB(ticker=ticker.lower()) for ticker in tickers]


class AnalyzeAll(LoadAllData):  # inherit from LoadAllData
    """
    Wrapper task for analyzing several or all stock data together
    example usage: AnalyzeAll(['aapl', 'goog', 'fb'])  #specific stock tickers
                   Analyze('all')  #load all data
    """

    def requires(self):
        tickers = allcashtags if self.tickers == "all" else self.tickers
        return [Analyze(ticker=ticker.lower()) for ticker in tickers]
