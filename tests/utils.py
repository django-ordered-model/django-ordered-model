# Query count helpers, copied from django source
# Added here for compatibility (django<3.1)
from django.db import DEFAULT_DB_ALIAS, connections
from django.test.utils import CaptureQueriesContext


class _AssertNumQueriesContext(CaptureQueriesContext):
    def __init__(self, test_case, num, connection):
        self.test_case = test_case
        self.num = num
        super().__init__(connection)

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        executed = len(self)
        self.test_case.assertEqual(
            executed,
            self.num,
            "%d queries executed, %d expected\nCaptured queries were:\n%s"
            % (
                executed,
                self.num,
                "\n".join(
                    "%d. %s" % (i, query["sql"])
                    for i, query in enumerate(self.captured_queries, start=1)
                ),
            ),
        )


def assertNumQueries(self, num, func=None, *args, using=DEFAULT_DB_ALIAS, **kwargs):
    conn = connections[using]

    context = _AssertNumQueriesContext(self, num, conn)
    if func is None:
        return context

    with context:
        func(*args, **kwargs)
