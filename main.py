from flask import Flask, render_template, request, Response
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
import env
import smtplib
import ssl
from io import BytesIO
import base64

def ping(url):
    try:
        response = requests.get(url, timeout=15)
        return response.status_code == 200
    except Exception:
        pass
    return False

def insert(availiable, site, cur, con):
    date = datetime.now().strftime(db_time)
    cur.execute(f"INSERT INTO availability VALUES('{date}', '{availiable}', '{site}')")
    con.commit()
    
def send_mail():
    try:
        port = 465 
        smtp_server = "smtp.gmail.com"
        sender_email = "hansaFlexMonitoring@gmail.com"
        receiver_email = (
            "frank.rogalski@hansa-flex.com", 
            "v.hinrichs@neusta.de", 
            "t.boettjer@neusta.de", 
            "c.junge@neusta.de", 
            "s.lohmann@neusta.de", 
            "dariusz.kurtycz@hansa-flex.com",
            "rika.stelljes@hansa-flex.com",
            "d.kessler@hansa-flex.com",
            "viktor.lipps@hansa-flex.com",
            "timo.wendt@hansa-flex.com",
            "juliemarie.garms@hansa-flex.com",
            "dario.gelzer@hansa-flex.com",
            "olga.kulesh@hec.de",
            "p.koehler@neusta.de"
        )
        message = """\
Subject: Prod Down
Moinsen,

das Produktivsystem ist gerade anscheinend down. Bitte prueft dies und erstellt gegebenenfalls ein Ticket wie in dem SAP Ticket https://launchpad.support.sap.com/#/incident/pointer/002075129500002491562021 beschrieben

Gruss
Frank's Python script"""

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, env.password)
            server.sendmail(sender_email, receiver_email, message)
    except Exception as e:
        app.logger.exception(e)

def check_availability():
    global last_send
    with sqlite3.connect(db_name) as con:
        url_to_check = "https://shop.hansa-flex.com/"
        sanity_url = "https://google.com"
        cur = con.cursor()
        while True:
            if not ping(sanity_url):
                insert("false", "google", cur, con)
            elif not ping(url_to_check):
                insert("false", "shop", cur, con)
                now = datetime.now()
                if last_send < now - timedelta(minutes=5):
                    send_mail()
                    last_send = now
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

def update_data(start, end):
    with sqlite3.connect(db_name) as con:
        start = datetime.strptime(start, usr_time).strftime(db_time)
        end = datetime.strptime(end, usr_time).strftime(db_time)
        df = pd.read_sql(f"SELECT * FROM availability WHERE date > '{start}' and date < '{end}'", con, parse_dates=["date"], index_col="date")
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
        ax.get_xaxis().set_major_formatter(DateFormatter(display_time))
        byte = BytesIO()
        ax.get_figure().savefig(byte, bbox_inches='tight', format="jpg")
        byte.seek(0)
        img = base64.b64encode(byte.read()).decode()
        plt.clf()
        max_index = data.index.max()
        newest_data = data[max_index]
        try:
            newest_data = newest_data.iloc[-1]
        except AttributeError:
            pass
        return options[newest_data], img, [i.strftime(display_time) for i in data[data == 0].index]

matplotlib.use('Agg')
db_name = "logs.db"
last_send = datetime.now() - timedelta(minutes=5)
db_time = "%Y-%m-%d %H:%M:%S"
usr_time = "%Y-%m-%dT%H:%M"
display_time = "%d.%m %H:%M"
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

@app.route('/', methods=['GET'])
def hello_world():
    start = request.args.get('start', default=(datetime.now() - timedelta(hours=24)).strftime(usr_time), type = str)
    end = request.args.get('end', default=datetime.now().strftime(usr_time), type = str)
    global up, last_update
    up, img, downtimes = update_data(start, end)
    return render_template('hello.html', up=up, img=img, downtimes=downtimes)

@app.route("/sendmail", methods=["POST"])
def sendmail():
    app.logger.warning("%s swag yolo", str(request.form.to_dict()))
    return Response(status=200)

if __name__ == '__main__':
    app.run(port=80, host="0.0.0.0")