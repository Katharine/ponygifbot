from gevent import monkey; monkey.patch_all()
import gevent
from flask import Flask, request, jsonify

import ponies
import settings

app = Flask(__name__)


@app.route('/telegram/update', methods=['POST'])
def handle_update():
    if 'inline_query' not in request.json:
        return 'u wot mate?'
    query = request.json['inline_query']
    gevent.spawn(ponies.handle_request, query['id'], query['query'])
    return ''


@app.route('/slack/command', methods=['POST'])
def handle_slack():
    pone = ponies.find_ponies(request.form['text'])
    if len(pone) == 0:
        return "No ponies found."
    url = pone[0]['representations']['small']
    return jsonify(attachments=[{
        "fallback": url,
        "image_url": "https:"+url,
        "title": request.form['text']
    }], text="", response_type="in_channel")


if __name__ == '__main__':
    from gevent.wsgi import WSGIServer
    http_server = WSGIServer(('', settings.PORT), app)
    http_server.serve_forever()
    # app.run(debug=True)
