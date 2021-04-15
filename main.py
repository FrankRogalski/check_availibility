from flask import Flask, render_template
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import FuncFormatter
from datetime import datetime, timedelta
import sqlite3
import requests
from time import sleep
from threading import Thread

def ping(url):
    try:
        response = requests.get(url, timeout=15)
        return response.status_code == 200
    except Exception:
        pass
    return False

def insert(availiable, site, cur, con):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(f"INSERT INTO availability VALUES('{date}', '{availiable}', '{site}')")
    con.commit()

def check_availability():
    with sqlite3.connect(db_name) as con:
        url_to_check = "https://shop.hansa-flex.com/"
        sanity_url = "https://google.com"
        cur = con.cursor()
        while True:
            if not ping(sanity_url):
                insert("false", "google", cur, con)
            elif not ping(url_to_check):
                insert("false", "shop", cur, con)
            else:
                insert("true", "shop", cur, con)
            sleep(60)

def type_to_number(line):
    if line["up"] == "true":
        return 1
    else:
        return 0 if line["site"] == "shop" else 0.5
    
def form(num, _):
    return {1: "Online", 0.5: "Lokale Probleme", 0: "Offline"}[num]

def update_data(now):
    with sqlite3.connect(db_name) as con:
        date = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        df = pd.read_sql(f"SELECT * FROM availability WHERE date > '{date}'", con, parse_dates=["date"])
        df.set_index("date", inplace=True)
        data = df.apply(type_to_number, axis=1)
        ax = data.plot(
            figsize=(20, 10),
            grid=True,
            legend=False,
            yticks=(0, 0.5, 1),
            title="Graph der System Verfügbarkeit",
            ylabel="System Verfügbarkeit",
            xlabel="Zeitpunkt",
            ylim=(-0.1, 1.1),
            rot=0,
        )
        ax.get_yaxis().set_major_formatter(FuncFormatter(form))
        ax.get_xaxis().set_major_formatter(DateFormatter("%d.%m %H:%M"))
        ax.get_figure().savefig("static/test.png", bbox_inches='tight')
        plt.clf()
        max_index = data.index.max()
        newest_data = data[max_index]
        try:
            newest_data = newest_data.iloc[-1]
        except AttributeError:
            pass
        return options[newest_data]

matplotlib.use('Agg')
db_name = "logs.db"
last_update = datetime.now() - timedelta(minutes=1)
up=None
options = {
    0: "Nein", 
    1: "Ja", 
    0.5: "Weiß nicht mein Internet ist down"
}
with sqlite3.connect(db_name) as con:
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS availability (date text, up boolean, site text)")
    cur.execute("CREATE INDEX IF NOT EXISTS availability_index on availability(date)")

Thread(target=check_availability).start()

app = Flask(__name__)

@app.route('/')
def hello_world():
    global up, last_update
    now = datetime.now()
    if last_update < now - timedelta(minutes=1):
        up = update_data(now)
        last_update = now
    return render_template('hello.html', up=up)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0")