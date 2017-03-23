#!/usr/bin/python3

import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
from flask import Flask, g, render_template, send_from_directory
from werkzeug.contrib.cache import SimpleCache

app = Flask(__name__)
cache = SimpleCache()

db_config = {
    "host": os.environ.get("POSTGRESQL_DEST_HOST") or "localhost",
    "port": os.environ.get("POSTGRESQL_DEST_PORT") or 5432,
    "user": os.environ.get("POSTGRESQL_DEST_USER") or "vainweb",
    "password": os.environ.get("POSTGRESQL_DEST_PASSWORD") or "vainweb",
    "dbname": os.environ.get("POSTGRESQL_DEST_DB") or "vainsocial-web"
}

def dbpool():
    if not hasattr(g, "db_pool"):
        g.db_pool = psycopg2.pool.ThreadedConnectionPool(
            **db_config, minconn=1, maxconn=10)
    return g.db_pool

@app.teardown_appcontext
def db_disconnect(err):
    if hasattr(g, "db_pool"):
        g.db_pool.closeall()

@app.context_processor
def sql_processor():
    def sql_val(query):
        val = cache.get(query)
        if val is not None:
            return val.get(0)

        con = dbpool().getconn()
        c = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

        c.execute(query)
        val = c.fetchone()
        cache.set(query, val, timeout=60*60)  # seconds

        c.close()
        dbpool().putconn(con)

        return val.get(0)

    return dict(sql_val=sql_val)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/assets/<path:path>")
def send_assets(path):
    return send_from_directory("templates/assets", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
