"""Setup our database and register both our base and all our tool models."""

import atexit
import logging
import time
import traceback
from argparse import Namespace
from pathlib import Path

from peewee import SqliteDatabase
from platformdirs import user_data_dir

from qyx.tools._models_ import Project, Request, Scan, State


class DebugSqliteDatabase(SqliteDatabase):
    """Instrument SQLite queries to find performance issues."""

    def __init__(self, *args, slow_threshold_ms=5.0, **kwargs):
        """..."""
        super().__init__(*args, **kwargs)
        self.slow_threshold_ms = slow_threshold_ms

    def execute_sql(self, sql, params=None):
        """Execute SQL and log slow/inefficient queries."""
        start = time.perf_counter()
        cursor = super().execute_sql(sql, params)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if elapsed_ms > self.slow_threshold_ms:
            # Show interpolated SQL for debugging
            interpolated = self._interpolate_sql(sql, params)

            print(f"\n⏱️  SLOW QUERY ({elapsed_ms:.2f}ms)")
            print(f"SQL: {interpolated}")
            print(f"Raw: {sql}")
            print(f"Params: {params}")

            # Show where in code this came from
            stack = traceback.extract_stack()
            for frame in reversed(stack[:-1]):  # Skip this frame
                if "/peewee" not in frame.filename and "/qyx/" in frame.filename:
                    print(f"Called from: {frame.filename}:{frame.lineno} in {frame.name}")
                    break

            # Analyze query plan
            self._analyze_query_plan(sql, params)

        return cursor

    def _interpolate_sql(self, sql: str, params: tuple | None) -> str:
        """Interpolate params into SQL for display (NOT for execution)."""
        if not params:
            return sql

        result = sql
        for param in params:
            # Simple replacement for debugging - good enough
            if isinstance(param, str):
                value = f"'{param}'"
            elif param is None:
                value = "NULL"
            else:
                value = str(param)
            result = result.replace("?", value, 1)
        return result

    def _analyze_query_plan(self, sql: str, params: tuple | None):
        """Show query plan and highlight issues."""
        try:
            plan = super().execute_sql("EXPLAIN QUERY PLAN " + sql, params)
            print("\nQuery Plan:")

            issues = []
            for row in plan.fetchall():
                detail = row[3]  # detail is 4th column
                print(f"  {detail}")

                if "SCAN TABLE" in detail:
                    issues.append(f"⚠️ {detail} → full table scan")

                if "ORDER BY" in detail:
                    issues.append(f"⚠️ {detail} → order by not using index - add composite index?")

                if "USE TEMP B-TREE FOR ORDER BY" in detail:
                    issues.append(f"⚠️ {detail} → sort without index")

                if "USE TEMP B-TREE FOR GROUP BY" in detail:
                    issues.append(f"⚠️ {detail} → group without index")

                if "AUTOMATIC INDEX" in detail:
                    issues.append(f"⚠️ {detail} → missing index")

            if issues:
                print("\nIssues found:")
                for issue in issues:
                    print(f"  {issue}")

        except Exception as e:
            print(f"Could not get query plan: {e}")


def setup_sqlite(args: Namespace) -> None:
    """Setup our db store, setting the db connection into args for subsequent use."""
    if "tools" not in args:
        raise RuntimeError("Sorry, setup/tools.py must have already been run before we can setup the database!")

    db_path = Path(user_data_dir("qyx")) / "db.sqlite3"  # Normal path..
    db_path = getattr(args, "db_path", db_path)  # Override primarily used to override db path for testing!

    # Only create parent directory for file-based databases
    db_path_name: str = db_path
    if db_path != ":memory:" and not str(db_path).startswith("file:"):
        db_path_name = db_path.name
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    db_ = DebugSqliteDatabase(
        db_path,
        pragmas={
            "autocommit": True,
            "check_same_thread": False,
            "foreign_keys": 1,
            "automatic_index": 1,
        },
        slow_threshold_ms=200.0,
    )

    # Now that we've created our connection, register to cleanly close it on exit.
    atexit.register(lambda: db_.close() if not db_.is_closed() else None)

    # Make sure our models have tables defined for 'em!
    models = [Project, Request, Scan, State]  # Base models first...
    for o_tool in args.tools.tools():  # Followed by tool-specific storage models
        for peewee_model_class in o_tool.get_models():
            models.append(peewee_model_class)

    # CORE! Tie the models defined to our database instance
    for model_class in models:
        model_class._meta.database = db_
        model_class.create_table(safe=True)

    log = logging.getLogger(__name__)
    args._db = db_  # Set for subsequent use (very few places though)
    log.info(f"...connected to {db_path_name=} with {len(models)} models defined.")
