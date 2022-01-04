from flask import Flask, render_template, request, Response
import pandas as pd
import env
import mail_sender
import requests
import json
import time

if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Authorization': '',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Referer': 'https://www.impfportal-niedersachsen.de/portal/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'TE': 'trailers',
    }

    params = (
        ('birthdate', '886244400000'),
    )
    app = Flask(__name__)

@app.route("/impfung", methods=["GET"])
def get_availibility():
    try:
        response = requests.get('https://www.impfportal-niedersachsen.de/portal/rest/publicFree/findVaccinationCenterListTicketAddrBP/28870', headers=headers, params=params)

        parsed = json.loads(response.content.decode('utf-8'))
        df = pd.DataFrame.from_records(parsed["resultList"])
        verden = df[df['city'] == 'Verden']
        if len(verden):
            earliest = time.strftime("am %d.%m.%y um %H:%M Uhr", time.localtime(verden.iloc[0]['earliestDate'] // 1000))
            return Response(f"Verden hat freie Impfplätze, der früheste ist {earliest}")
        else:
            return Response("Verden hat momentan keine freien Impfplätze")
    except Exception as ex:
        app.logger.warn(ex)
        return Response("Fehler beim Seitenaufruf, bitte Frank bescheid geben", status=400)

@app.route("/sendmail", methods=["POST"])
def sendmail():
    data = request.get_json(force=True)
    if data['password'] == env.mail_password and len(data.keys()) == 4:
        del data['password']
        app.logger.warn('%s data', str(data))
        try:
            mail_sender.send_mail(**data)
        except Exception as e:
            app.logger.warn(e)
            return Response(status=510)
        return Response(status=201)
    return Response(status=401)



if __name__ == '__main__':
    if 'cert' in vars(env).keys():
        context = (env.cert, env.key)
        port = 443
    else:
        context = None
        port = 80
    app.run(port=port, host="0.0.0.0", ssl_context=context)
