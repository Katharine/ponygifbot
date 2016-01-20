from gevent import monkey; monkey.patch_all()
import gevent
from flask import Flask, request

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

if __name__ == '__main__':
    from gevent.wsgi import WSGIServer
    http_server = WSGIServer(('', settings.PORT), app)
    http_server.serve_forever()
    # app.run(debug=True)
