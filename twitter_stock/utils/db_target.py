from luigi import Target
from sqlalchemy import engine


class SQLiteTableTarget(Target):
    """
    Luigi target of SQLite database tables
    """

    def __init__(self, table: str, eng: engine.Engine):
        super().__init__()
        self._table = table
        self._eng = eng

    def exists(self):
        """
        Override exists method. Luigi will check to see if task needs to run
        """
        query = """SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}' """
        query_set = self._eng.execute(query.format(table_name=self._table))
        return query_set.fetchone() is not None
