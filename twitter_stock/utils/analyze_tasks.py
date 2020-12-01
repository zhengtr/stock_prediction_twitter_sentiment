from luigi.mock import MockTarget
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from .loaddata_tasks import *


class Analyze(Task):
    """
    Analyze twitter's content by sentiment, and use random forest classifier to train model.
    """

    engine = create_engine(os.environ["DATABASE_URL"])
    ticker = Parameter()

    def requires(self):
        return ExtracttoDB(self.ticker)

    def output(self):
        return SQLiteTableTarget(
            table="{}_predict".format(self.ticker), eng=self.engine
        )

    def run(self):
        # get data from db
        analyze = pd.read_sql_query(
            """SELECT * FROM {}""".format(self.ticker),
            con=self.engine,
            parse_dates=["Date"],
        )
        # align dates (predict occurs on the next day)
        analyze["signal"] = analyze["signal"].shift(-1, fill_value=0)
        # splitting data for train and predict
        train = analyze[analyze["Date"] <= "2016-05-31"]
        predict = analyze[
            (analyze["Date"] > "2016-05-25") & (analyze["Date"] < "2016-06-16")
        ]
        x_train, x_test, y_train, y_test = train_test_split(
            np.array(train[["sentiment"]]),
            np.array(train[["signal"]]),
            test_size=0.2,
            random_state=40,
        )
        # train model
        model = RandomForestClassifier(random_state=40)
        model.fit(x_train, y_train)
        # get predict result and send back to db
        predict["signal_predict"] = model.predict(np.array(predict[["sentiment"]]))
        predict.to_sql(
            "{}_predict".format(self.ticker),
            con=self.engine,
            if_exists="replace",
            index=False,
        )


class Predict(Task):
    """
    Predict the result using trained model.
    """

    engine = create_engine(os.environ["DATABASE_URL"])
    ticker = Parameter()
    date = Parameter()

    def requires(self):
        return Analyze(self.ticker)

    def output(self):
        # use mock target to save the output, desired output type str
        return MockTarget("predict_result")

    def run(self):
        # get query from db
        predict = pd.read_sql_query(
            '''SELECT date, signal_predict FROM {}_predict WHERE date LIKE "{}%"'''.format(
                self.ticker, self.date
            ),
            con=self.engine,
            parse_dates=["Date"],
        )
        result = "BUY" if predict["signal_predict"][0] == 1 else "SELL"
        text = 'For {}, the predicted result for "{}" is {}!'.format(
            self.date, self.ticker.upper(), result
        )
        with self.output().open("w") as f:
            f.write(text)

    def get_result(self):
        # get result back as str from mocktarget
        with self.output().open("r") as f:
            result = f.read()
        return result
