from flask import Flask, render_template, request, Response
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import FuncFormatter
from datetime import datetime, timedelta
import sqlite3
from io import BytesIO
import base64
import os
import sys
import env

def type_to_number(line):
    if line["up"] == "true":
        return 1
    else:
        return 0 if line["site"] == "shop" else 0.5
    
def form(num, _):
    return {1: "Online", 0.5: "Lokale Probleme", 0: "Offline"}[num]

def read_data(start, end):
    start = datetime.strptime(start, usr_time).strftime(db_time)
    end = datetime.strptime(end, usr_time).strftime(db_time)
    with sqlite3.connect(db_name) as con:
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
    f = ax.get_figure()
    f.canvas.start_event_loop(sys.float_info.min)
    f.savefig(byte, bbox_inches='tight', format="jpg")
    byte.seek(0)
    img = base64.b64encode(byte.read()).decode()
    f.clear()
    plt.close(f)
    max_index = data.index.max()
    newest_data = data[max_index]
    try:
        newest_data = newest_data.iloc[-1]
    except AttributeError:
        pass
    return options[newest_data], img, [i.strftime(display_time) for i in data[data == 0].index]

if __name__ == '__main__':
    matplotlib.use('Agg')
    path = os.path.dirname(__file__)
    db_name = os.path.join(path, "logs.db")
    db_time = "%Y-%m-%d %H:%M:%S"
    usr_time = "%Y-%m-%dT%H:%M"
    display_time = "%d.%m %H:%M:%S"
    options = {
        0: "Nein", 
        1: "Ja", 
        0.5: "Vielleicht, momentan existieren lokale Probleme"
    }
    with sqlite3.connect(db_name) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS availability (date text, up boolean, site text)")
        cur.execute("CREATE INDEX IF NOT EXISTS availability_index on availability(date)")

    app = Flask(__name__)

@app.route('/', methods=['GET'])
def get_uptime():
    start = request.args.get('start', default=(datetime.now() - timedelta(hours=24)).strftime(usr_time), type = str)
    end = request.args.get('end', default=datetime.now().strftime(usr_time), type = str)
    up, img, downtimes = read_data(start, end)
    return render_template('hello.html', up=up, img=img, downtimes=downtimes)

@app.route("/sendmail", methods=["POST"])
def sendmail():
    app.logger.warning("%s swag yolo", str(request.form.to_dict()))
    return Response(status=200)

if __name__ == '__main__':
    app.run(port=443, host="0.0.0.0", ssl_context=(env.cert, env.key))