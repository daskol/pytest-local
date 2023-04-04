#!/usr/bin/env python
"""Simple testing server based on PyTest. Its design goal is to preloaded list
of modules. It can be very useful in work with JAX/TensorFlow or any other
library which takes a significant time to load.

NOTE It uses a forkserver multiprocessing context. It can potentially cause
some issues with shared state.
"""

import logging
from argparse import REMAINDER, ArgumentParser, Namespace
from http import HTTPStatus
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, HTTPServer
from json import dumps, load, loads
from multiprocessing import get_context
from threading import Thread
from urllib.parse import parse_qs, urlparse, urlunparse


def run_pytest(args):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    logging.info('run pytest in in-process mode: %s', args)
    import pytest
    code = pytest.main(args)
    logging.info('exit code is %s', code)
    return code


class Context:

    def __init__(self, module_names: list[str]):
        self.module_names = module_names
        self.reset()

    def reset(self, method='forkserver'):
        self.mp_context = get_context(method)
        self.mp_context.set_forkserver_preload(self.module_names)

    def submit(self, fn, *args, **kwargs):
        child = self.mp_context.Process(target=fn, args=args, kwargs=kwargs)
        child.start()
        child.join()
        return child.exitcode


class HTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/ping':
            return self.ping()

    def do_POST(self):
        self.context: Context = self.server.context
        url = urlparse(self.path)
        params = parse_qs(url.query)
        if url.path == '/restart':
            return self.restart(params)
        elif url.path == '/run':
            return self.run(params)
        elif url.path == '/shutdown':
            return self.shutdown()

    def ping(self):
        body = b'Pong.\n'
        self.send_response(HTTPStatus.OK)
        self.send_header('content-length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def restart(self, params):
        method = params.get('method', ['forkserver'])[0]
        if method not in ('fork', 'forkserver', 'spawn'):
            return self.fail(HTTPStatus.BAD_REQUEST)
        self.context.reset()
        self.fail(HTTPStatus.OK)

    def fail(self, status_code):
        self.send_response(status_code)
        self.end_headers()

    def run(self, params):
        req_size = int(self.headers.get('content-length', 0))
        req_body = self.rfile.read(req_size)

        json = loads(req_body)
        args = json.get('args', [])
        code = self.context.submit(run_pytest, args)
        json = {'code': code}
        body = dumps(json, ensure_ascii=False).encode('utf-8')

        self.send_response(HTTPStatus.OK)
        self.send_header('content-length', len(body))
        self.send_header('content-type', 'application/json; utf-8')
        self.end_headers()
        self.wfile.write(body)

    def shutdown(self):
        self.fail(HTTPStatus.OK)
        th = Thread(target=self.server.shutdown)
        th.start()


def serve(host: str, port: int, module_names: list[str]):
    logging.info('create multiprocessing context')
    context = Context(module_names)
    logging.info('start testing server on %s:%d', host, port)
    server = HTTPServer((host, port), HTTPRequestHandler)
    server.context = context
    server.serve_forever()


def run(host: str, port: int, args: list[str]):
    logging.info('submit testing request to %s:%d', host, port)
    url = urlunparse(['http', f'{host}:{port}', '/run', '', '', ''])
    body = dumps({'args': args}, ensure_ascii=False)
    sess = HTTPConnection(host, port, timeout=120)
    sess.request('POST', url, body)
    resp = sess.getresponse()

    if (code := resp.getcode()) != HTTPStatus.OK:
        logging.info('response failed with status code %d', code)
        return

    json = load(resp)
    if (code := json.get('code')):
        logging.info('testing was failed with exit code %d', code)
        return

    logging.info('testing was successfully completed')


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)

    ns: Namespace = parser.parse_args()
    if ns.args and ns.args[0] == '--':
        ns.args = ns.args[1:]
    if ns.listen:
        serve(ns.host, ns.port, ns.module_name)
    else:
        run(ns.host, ns.port, ns.args)


parser = ArgumentParser()
parser.add_argument('-H',
                    '--host',
                    default='127.0.0.1',
                    help='TCP address to listen (default: 127.0.0.1)')
parser.add_argument('-p',
                    '--port',
                    type=int,
                    default=7070,
                    help='TCP port to listen (default: 7070)')
parser.add_argument('-l',
                    '--listen',
                    default=False,
                    action='store_true',
                    help='run in testing server mode')
parser.add_argument('-m',
                    '--module-name',
                    default=[],
                    action='append',
                    help='list of modules to preload')
parser.add_argument('args',
                    nargs=REMAINDER,
                    help='arguments to pass to pytest')


if __name__ == '__main__':
    main()
