# Force Chroma to use a newer SQLite build on environments with old sqlite3
try:
    import pysqlite3  # noqa: F401
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except Exception:
    pass
