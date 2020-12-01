import pandas as pd
from sqlalchemy import create_engine
import os

# import matplotlib.pyplot as plt


def graph(ticker):
    """
    Helper function to return data for graphing
    """
    engine = create_engine(os.environ["DATABASE_URL"])
    data = pd.read_sql_query(
        """SELECT Date, pct_change, signal_predict FROM {}_predict""".format(ticker),
        con=engine,
        parse_dates=["Date"],
    )
    data.iloc[0, 1] = 0.0
    data["signal_predict"] = (
        data["signal_predict"].replace(0, -1).shift(1, fill_value=0)
    )
    data["nav"] = data["pct_change"].cumsum()
    data["nav_strategy"] = (data["pct_change"] * data["signal_predict"]).cumsum()
    # df = data[['nav', 'nav_strategy']]
    # df.plot()
    # plt.show()
    # engine.disposal
    date = data["Date"].astype(str).to_list()
    nav = data["nav"].to_list()
    nav_strategy = data["nav_strategy"].to_list()
    return date, nav, nav_strategy
