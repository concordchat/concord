import multiprocessing
import os
import threading
import orjson
import logging
import sys
from flask import Flask, Response, send_from_directory, send_file
from .ratelimiter import limiter
from .randoms import _id, code

try:
    import uvloop # type: ignore
    uvloop.install()
except:
    pass

app = Flask(__name__)
limiter.init_app(app)
logging.basicConfig(level=logging.DEBUG)

@app.route('/__development/ping')
async def ping():
    return orjson.dumps({'cookie': 'pong!'})

@app.route('/__development/uuid')
async def uuid():
    return orjson.dumps({'id': _id()})

@app.route('/__development/u-id')
async def s_id():
    return orjson.dumps({'id': code()})

@app.route('/favicon.ico')
async def _get_icon():
    return send_file(os.path.join(app.root_path, 'static', 'favicon.ico'), 'image/vnd.microsoft.icon')

@app.errorhandler(404)
async def _not_found(*args):
    return orjson.dumps({'code': 0, 'message': '404: Not Found'})

@app.errorhandler(500)
async def _internal_error(*args):
    return orjson.dumps({'code': 0, 'message': '500: Internal Server Error'})

@app.errorhandler(429)
async def _ratelimited(*args):
    return orjson.dumps({'code': 0, 'message': '429: Too Many Requests'})

@app.after_request
async def _after_request(resp: Response):
    resp.headers['content_type'] = 'application/json'
    resp.headers.remove('Retry-After')
    try:
        print(resp.status, resp.get_data(), threading.current_thread().ident, multiprocessing.current_process().ident, file=sys.stderr)
    except:
        pass
    return resp

if __name__ == '__main___':
    app.run(debug=True)
