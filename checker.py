import requests
from time import sleep
import sqlite3
from datetime import datetime, timedelta
import env
import logging
import os
import threading
import mail_sender

def ping(url):
    try:
        response = requests.get(url, timeout=15)
        return response.status_code // 100 in (2, 3)
    except:
        pass
    return False

def insert(availiable, site):
    with sqlite3.connect(db_name) as con:
        cur = con.cursor()
        date = datetime.now().strftime(db_time)
        cur.execute(f"INSERT INTO availability VALUES('{date}', '{availiable}', '{site}')")
        con.commit()

def send_mail():
    try:
        mail_sender.send_mail(receiver_emails, "Prod Down", message)
    except Exception as e:
        logging.error("Error sending mail %s", e)

message = """\
Moinsen,

das Produktivsystem ist gerade anscheinend down. Bitte prueft dies und erstellt gegebenenfalls ein Ticket wie in dem SAP Ticket https://launchpad.support.sap.com/#/incident/pointer/002075129500002491562021 beschrieben

Gruss
Frank's Python script"""
receiver_emails = (
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

url_to_check = "https://shop.hansa-flex.com/"
sanity_url = "https://google.com"
path = os.path.dirname(__file__)
db_name = os.path.join(path, "logs.db")
last_send = datetime.now() - timedelta(minutes=5)

def write_db():
    global last_send
    if not ping(sanity_url):
        insert("false", "google")
    elif not ping(url_to_check):
        insert("false", "shop")
        now = datetime.now()
        if last_send < now - timedelta(minutes=5):
            send_mail()
            last_send = now
    else:
        insert("true", "shop")

if __name__ == "__main__":
    with sqlite3.connect(db_name) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS availability (date text, up boolean, site text)")
        cur.execute("CREATE INDEX IF NOT EXISTS availability_index on availability(date)")
    logging.basicConfig(
        filename='log.txt',
        level=logging.INFO, 
        datefmt="%Y-%m-%d %H:%M:%S", 
        format="%(asctime)s %(levelname)-8s %(message)s"
    )
    db_time = "%Y-%m-%d %H:%M:%S"
    while True:
        threading.Thread(target=write_db).start()
        sleep(15)