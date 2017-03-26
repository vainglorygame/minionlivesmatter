#!/usr/bin/python3

import os
import psycopg2
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

data = {}

def update_vals():
    con = psycopg2.connect(**db_config)
    c = con.cursor()

    def sql_val(query):
        c.execute(query)
        return c.fetchone()[0]

    data["turrets_rebuilt"] = sql_val("SELECT SUM(turret_kills) FROM participant WHERE created_at > NOW() - '1 day'::INTERVAL")
    data["minions_for_nothing"] = sql_val("SELECT SUM(minion_kills) FROM participant WHERE NOT winner AND created_at > NOW() - '1 day'::INTERVAL")
    data["minions_total"] = sql_val("SELECT SUM(minion_kills) FROM participant WHERE created_at > NOW() - '1 day'::INTERVAL")
    data["fountains_wasted"] = sql_val("SELECT COUNT((item_grants->>'*1045_Item_FountainOfRenewal*')::INT)-COUNT((item_uses->>'*1045_Item_FountainOfRenewal*')::INT) FROM participant WHERE created_at > NOW() - '1 day'::INTERVAL")
    data["crystal_sentries"] = sql_val("SELECT SUM(participant.crystal_mine_captures) FROM participant WHERE participant.created_at > NOW() - '1 day'::INTERVAL")
    data["flares_sold"] = sql_val("SELECT SUM((participant.item_sells->>'*1038_Item_Flare*')::INT) FROM participant WHERE participant.created_at > NOW() - '1 day'::INTERVAL")
    data["minions_per_kraken"] = sql_val("SELECT (SUM(match.duration)/60*5) / SUM(roster.kraken_captures) FROM match JOIN roster ON roster.match_api_id=match.api_id WHERE match.created_at > NOW() - '1 day'::INTERVAL")
    data["minion_candies"] = sql_val("SELECT SUM((item_uses->>'*1041_Item_MinionCandy*')::INT) FROM participant WHERE created_at > NOW() - '1 day'::INTERVAL")
    data["infusions_secs"] = sql_val("SELECT (24*60*60) / (SUM((participant.item_uses->>'*1052_Item_WeaponInfusion*')::INT) + SUM((participant.item_uses->>'*1053_Item_CrystalInfusion*')::INT))::FLOAT FROM participant JOIN roster ON participant.roster_api_id=roster.api_id JOIN match ON roster.match_api_id=match.api_id WHERE participant.created_at > NOW() - '1 day'::INTERVAL")
    data["scout_traps"] = sql_val("SELECT SUM((item_uses->>'*1054_Item_ScoutTrap*')::INT) FROM participant WHERE participant.created_at > NOW() - '1 day'::INTERVAL")
    data["saw_turrets"] = sql_val("SELECT SUM(turret_kills) FROM participant WHERE hero='*SAW*' AND created_at > NOW() - '1 day'::INTERVAL")
    data["matches"] = sql_val("SELECT COUNT(*) FROM match WHERE created_at > NOW() - '1 day'::INTERVAL")
    data["minions_min"] = sql_val("SELECT SUM(minion_kills)/(24*60*60)::FLOAT FROM participant WHERE participant.created_at > NOW() - '1 day'::INTERVAL")
    data["vox_minionkills"] = sql_val("SELECT SUM(minion_kills) FROM participant WHERE hero='*Vox*' AND created_at > NOW() - '1 day'::INTERVAL")
    data["minionfeet"] = sql_val("SELECT SUM((item_grants->>'*1080_Item_MinionsFoot*')::INT) FROM participant WHERE created_at > NOW() - '1 day'::INTERVAL")

    c.close()

@app.route("/")
def index():
    return render_template("index.html", data=data)

@app.route("/update")
def update():
    update_vals()
    return render_template("index.html", data=data)

@app.route("/assets/<path:path>")
def send_assets(path):
    return send_from_directory("templates/assets", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
