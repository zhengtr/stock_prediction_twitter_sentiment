from unittest import TestCase
from django.test import TestCase as DJTest, RequestFactory
from tempfile import TemporaryDirectory
import boto3
import pytest
import xlsxwriter
from moto import mock_s3
from twitter_stock.utils.analyze_tasks import *
from twitter_stock.utils.my_request import *
from sqlalchemy import create_engine


mockBucket = "mockBucket"
s3 = "s3://{}".format(mockBucket)


class MockUploadFinanceData(UploadFinanceData):
    def output(self):
        return S3Target(
            os.path.join(s3, "FinanceData", "{}.parquet".format(self.ticker))
        )


class MockTwittwer(Task):
    def output(self):
        return LocalTarget("data/LocalTwitter/aal.parquet")


class MockFinance(Task):
    def output(self):
        return LocalTarget("data/FinanceData/aal.parquet")


class MockExtracttoDB(ExtracttoDB):
    engine = create_engine("sqlite:///django.db.backends.sqlite3")

    def requires(self):
        return {
            "twitter": MockTwittwer(),
            "finance": MockFinance(),
        }


class MockAnalyze(Analyze):
    engine = create_engine("sqlite:///django.db.backends.sqlite3")

    def requires(self):
        return MockExtracttoDB(self.ticker)


class MockPredict(Predict):
    engine = create_engine("sqlite:///django.db.backends.sqlite3")

    def requires(self):
        return MockAnalyze(self.ticker)


@mock_s3
class LuigiDataTests(TestCase):
    def setUp(self):
        # Mock boto3.client
        client = boto3.client(
            "s3",
            region_name="us-west-1",
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
        )
        # Mock create bucket
        client.create_bucket(Bucket=mockBucket)
        # Add files to bucket
        # client.put_object(Bucket=mockBucket, Key="images/{}".format(mockFiles[0]))
        # client.put_object(Bucket=mockBucket, Key="saved_models/{}".format(mockFiles[1]))

    def tearDown(self):
        s3 = boto3.resource(
            "s3",
            region_name="us-west-1",
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
        )
        # Delete files
        bucket = s3.Bucket(mockBucket)
        # Delete bucket
        for x in bucket.objects.all():
            x.delete()
        s3.Bucket(mockBucket).delete()

    def test_upload_finance_data(self):

        res = build([MockUploadFinanceData("aal")], local_scheduler=True)
        # test if task ran successfully and desired output
        self.assertTrue(res)
        self.assertEqual(
            MockUploadFinanceData("aal").output().path,
            "s3://mockBucket/FinanceData/aal.parquet",
        )

    def test_local_twitter_data(self):
        with TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "export_dashboard_aal_123.xlsx"), "a").close()

            class MockLocalTwitterData(LocalTwitterData):
                def output(self):
                    file = glob.glob(
                        os.path.join(
                            tmp, "export_dashboard_{}*.xlsx".format(self.ticker)
                        )
                    )[0]
                    return LocalTarget(file)

            res = build([MockLocalTwitterData("aal")], local_scheduler=True)
            # test if task ran successfully and desired output
            self.assertTrue(res)
            self.assertEqual(
                MockLocalTwitterData("aal").output().path,
                os.path.join(tmp, "export_dashboard_aal_123.xlsx"),
            )

    def test_upload_twitter_data(self):
        with TemporaryDirectory() as tmp:
            workbook = xlsxwriter.Workbook(
                os.path.join(tmp, "export_dashboard_aal_123.xlsx")
            )
            worksheet = workbook.add_worksheet("Stream")
            worksheet.write(0, 0, "Date")
            worksheet.write(1, 0, "2020-01-01")
            workbook.close()

            class MockLocalTwitterData(LocalTwitterData):
                def output(self):
                    file = glob.glob(
                        os.path.join(
                            tmp, "export_dashboard_{}*.xlsx".format(self.ticker)
                        )
                    )[0]
                    return LocalTarget(file)

            class MockUploadTwitterData(UploadTwitterData):
                def requires(self):
                    return MockLocalTwitterData(self.ticker)

                def output(self):
                    return S3Target(
                        os.path.join(
                            s3, "TwitterData", "{}.parquet".format(self.ticker)
                        )
                    )

            res = build([MockUploadTwitterData("aal")], local_scheduler=True)
            # test if task ran successfully and desired output
            self.assertTrue(res)
            self.assertEqual(
                MockUploadTwitterData("aal").output().path,
                "s3://mockBucket/TwitterData/aal.parquet",
            )

    def test_local_cashtags(self):
        with TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "NASDAQ_100_cashtags.txt"), "w") as f:
                f.write("aal\naapl")

            class MockLocalCashtags(LocalCashtags):
                def output(self):
                    file = os.path.join(tmp, "NASDAQ_100_cashtags.txt")
                    return LocalTarget(file)

            res = build([MockLocalCashtags()], local_scheduler=True)
            # test if task ran successfully and desired output
            self.assertTrue(res)
            self.assertEqual(
                MockLocalCashtags().output().path,
                os.path.join(tmp, "NASDAQ_100_cashtags.txt"),
            )
            self.assertEqual(MockLocalCashtags().get_cashtags(), ["aal", "aapl"])

    def test_upload_cashtags(self):
        with TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "NASDAQ_100_cashtags.txt"), "w") as f:
                f.write("aal\naapl")

            class MockLocalCashtags(LocalCashtags):
                def output(self):
                    file = os.path.join(tmp, "NASDAQ_100_cashtags.txt")
                    return LocalTarget(file)

            class MockUploadCashtags(UploadCashtags):
                def requires(self):
                    return MockLocalCashtags()

                def output(self):
                    return S3Target(os.path.join(s3, "NASDAQ_100_cashtags.txt"))

            res = build([MockUploadCashtags()], local_scheduler=True)
            self.assertTrue(res)
            self.assertEqual(
                MockUploadCashtags().output().path,
                "s3://mockBucket/NASDAQ_100_cashtags.txt",
            )


class CleanDataTest(TestCase):
    def test_clean_finance(self):
        test = list(dask.compute(clean_finance("data/FinanceData/aal.parquet")))[0]
        self.assertEqual(len(test), 78)
        self.assertListEqual(list(test.columns), ["Date", "pct_change"])

    def test_clean_twitter(self):
        test = list(dask.compute(clean_twitter("data/LocalTwitter/aal.parquet")))[0]
        self.assertEqual(list(test.columns), ["Date", "sentiment"])
        self.assertEqual(sum(test["sentiment"].isnull()), 0)

    def test_twitter_finance(self):
        test = dask.compute(
            twitter_finance(
                "data/FinanceData/aal.parquet", "data/LocalTwitter/aal.parquet"
            )
        )[0]
        self.assertEqual(len(test), 78)
        self.assertEqual(
            list(test.columns), ["Date", "sentiment", "pct_change", "signal"]
        )


class LuigiDBTest(TestCase):
    @pytest.mark.django_db
    def test_extract_to_db(self):

        res = build([MockExtracttoDB("aal")], local_scheduler=True)
        self.assertTrue(res)
        test = pd.read_sql_query(
            """SELECT * FROM aal""",
            con=create_engine("sqlite:///django.db.backends.sqlite3"),
        )
        self.assertTrue(test is not None)
        self.assertEqual(len(test), 78)

    @pytest.mark.django_db
    def test_anaylyze(self):

        res = build([MockAnalyze("aal")], local_scheduler=True)
        self.assertTrue(res)
        test = pd.read_sql_query(
            """SELECT * FROM aal_predict""",
            con=create_engine("sqlite:///django.db.backends.sqlite3"),
        )
        self.assertTrue(test is not None)
        self.assertEqual(len(test), 21)
        self.assertListEqual(
            list(test.columns),
            ["Date", "sentiment", "pct_change", "signal", "signal_predict"],
        )

    @pytest.mark.django_db
    def test_predict(self):
        res = build(
            [MockPredict(ticker="aal", date="2016-06-12")], local_scheduler=True
        )
        self.assertTrue(res)
        self.assertEqual(
            MockPredict(ticker="aal", date="2016-06-12").get_result(),
            'For 2016-06-12, the predicted result for "AAL" is SELL!',
        )


class LuigiTargetTest(TestCase):
    engine = create_engine("sqlite:///django.db.backends.sqlite3")

    def test_sqlite_target(self):
        test = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6]]), columns=["a", "b", "c"])
        test.to_sql("test", con=self.engine, if_exists="replace", index=False)
        target = SQLiteTableTarget("test", self.engine)
        self.assertTrue(target.exists())


class DjangoTest(DJTest):
    def test_basic_views(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/twitter_stock").status_code, 301)
        self.assertEqual(self.client.get("/fake").status_code, 404)

    def test_loadingData_view(self):
        req = RequestFactory().get("/twitter_stock/loadingData/")
        resp = loadingData(req)
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.content, b"")
