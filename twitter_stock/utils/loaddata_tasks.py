import yfinance as yf
import numpy as np
import os
import glob
from sqlalchemy import create_engine
from luigi import Task
from luigi.local_target import LocalTarget
from luigi.contrib.s3 import S3Target
from luigi.parameter import Parameter

from .db_target import SQLiteTableTarget
from .clean import *


s3_root = "s3://*****"  # add s3 bucket before running
local_root = os.path.abspath("data")


class UploadFinanceData(Task):
    """
    Pull stock data through yfinance, and upload to S3 bucket as parquet files.
    """

    ticker = Parameter()

    def output(self):
        # test from local file (development use)
        # return LocalTarget(
        #     os.path.join(local_root, "FinanceData", "{}.parquet".format(self.ticker)),
        #     format=Nop,
        # )
        return S3Target(
            os.path.join(s3_root, "FinanceData", "{}.parquet".format(self.ticker))
        )

    def run(self):
        finance = yf.download(
            self.ticker, start="2016-04-01", end="2016-06-17", progress=False
        )
        finance = finance.reset_index()
        finance.to_parquet(self.output().path)


class LocalTwitterData(Task):
    """
    Load from local 'TwitterData' directory
    Note: change this to use twitter API if available
    """

    ticker = Parameter()

    def output(self):
        file = glob.glob(
            os.path.join(
                local_root,
                "TwitterData",
                "export_dashboard_{}*.xlsx".format(self.ticker),
            )
        )[0]
        return LocalTarget(file)


class UploadTwitterData(Task):
    """
    Read local excel files of twitter archives, and upload to S3 bucket as parquet files.
    """

    ticker = Parameter()

    def requires(self):
        return LocalTwitterData(self.ticker)

    def output(self):
        return S3Target(
            os.path.join(s3_root, "TwitterData", "{}.parquet".format(self.ticker))
        )
        # test from local file (development use)
        # return LocalTarget(
        #     os.path.join(local_root, "LocalTwitter", "{}.parquet".format(self.ticker))
        # )

    def run(self):
        tmp = pd.read_excel(
            self.input().path, sheet_name="Stream", parse_dates=["Date"]
        )
        tmp.to_parquet(self.output().path)


class LocalCashtags(Task):
    """
    Load from local txt file that contains all cashtags
    """

    def output(self):
        file = os.path.join(local_root, "NASDAQ_100_cashtags.txt")
        return LocalTarget(file)

    def get_cashtags(self):
        return list(np.loadtxt(self.output().path, dtype=str, delimiter="\n"))


class UploadCashtags(Task):
    """
    Read local cashtags file, and upload to S3 bucket as txt file.
    """

    def requires(self):
        return LocalCashtags()

    def output(self):
        return S3Target(os.path.join(s3_root, "NASDAQ_100_cashtags.txt"))
        # test from local file (development use)
        # return LocalTarget(os.path.join(local_root, 'NASDAQ_100_cashtags.txt'))

    def run(self):
        tmp = list(np.loadtxt(self.input().path, dtype=str, delimiter="\n"))
        with self.output().open("w") as f:
            for item in tmp:
                f.write("{}\n".format(item))


class ExtracttoDB(Task):
    """
    Clean data and save to database
    """

    engine = create_engine(os.environ["DATABASE_URL"])
    ticker = Parameter()

    def requires(self):
        return {
            "twitter": UploadTwitterData(self.ticker),
            "finance": UploadFinanceData(self.ticker),
        }

    def output(self):
        return SQLiteTableTarget(table=self.ticker, eng=self.engine)

    def run(self):
        data = list(
            dask.compute(
                twitter_finance(
                    self.input()["finance"].path, self.input()["twitter"].path
                )
            )
        )[0]
        data.to_sql(self.ticker, con=self.engine, if_exists="replace", index=False)
