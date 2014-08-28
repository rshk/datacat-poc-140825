import os
import random
import time
from urlparse import urlparse, urljoin

import requests
import pytest

from datacat.db import create_tables, connect


POSTGRES_ENV_NAME = 'POSTGRES_URL'


@pytest.fixture(scope='module')
def postgres_conf():
    if POSTGRES_ENV_NAME not in os.environ:
        raise RuntimeError(
            "Missing configuration: the {0} environment variable is required"
            " in order to be able to create a PostgreSQL database for running"
            " tests. Please set it to something like: ``postgresql://"
            "user:password@host:port/database``."
            .format(POSTGRES_ENV_NAME))
    url = urlparse(os.environ[POSTGRES_ENV_NAME])
    return {
        'database': url.path.split('/')[1],
        'user': url.username,
        'password': url.password,
        'host': url.hostname,
        'port': url.port or 5432,
    }


@pytest.fixture(scope='module')
def postgres_admin_db(request, postgres_conf):
    conn = connect(**postgres_conf)

    def cleanup():
        conn.close()

    request.addfinalizer(cleanup)
    return conn


@pytest.fixture(scope='module')
def postgres_user_conf(request, postgres_conf):
    conn = connect(**postgres_conf)

    randomcode = random.randint(0, 999999)
    name = 'dtctest_{0:06d}'.format(randomcode)

    # Note: we need to use separate transactions to perform
    # administrative activities such as creating/dropping databases
    # and roles.

    # For this reason, we need to set the connection isolation level
    # to "autocommit"

    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute("""
        CREATE ROLE "{name}" LOGIN
        PASSWORD %(password)s;
        """.format(name=name), dict(password=name))

        cur.execute("""
        CREATE DATABASE "{name}"
        WITH OWNER "{name}"
        ENCODING = 'UTF-8';
        """.format(name=name))

    def cleanup():
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute('DROP DATABASE "{name}";'.format(name=name))
            cur.execute('DROP ROLE "{name}";'.format(name=name))

    request.addfinalizer(cleanup)

    conf = postgres_conf.copy()
    conf['user'] = name
    conf['password'] = name
    conf['database'] = name
    return conf


@pytest.fixture
def postgres_user_db(request, postgres_user_conf):
    conn = connect(**postgres_user_conf)

    def cleanup():
        conn.close()

    request.addfinalizer(cleanup)

    return conn


@pytest.fixture
def app_config(postgres_user_conf):
    from flask.config import Config
    from datacat.settings import default

    conf = Config('')
    conf.from_object(default)
    conf['DEBUG'] = False
    conf['DATABASE'] = postgres_user_conf
    return conf


class RunningAppInfo(object):
    def __init__(self, url, app):
        self.url = url
        self.app = app

    def make_url(self, path):
        return urljoin(self.url, path)

    def request(self, method, url, *a, **kw):
        return requests.request(method, self.make_url(url), *a, **kw)

    def get(self, url, *a, **kw):
        return self.request('GET', url, *a, **kw)

    def post(self, url, *a, **kw):
        return self.request('POST', url, *a, **kw)

    def put(self, url, *a, **kw):
        return self.request('PUT', url, *a, **kw)

    def patch(self, url, *a, **kw):
        return self.request('PATCH', url, *a, **kw)

    def delete(self, url, *a, **kw):
        return self.request('DELETE', url, *a, **kw)


@pytest.fixture
def running_app(request, app_config):
    # Run the application in a subprocess on a random port
    import multiprocessing
    from datacat.web import app

    app.config.update(app_config)

    create_tables(connect(**app.config['DATABASE']))

    HOST, PORT = '127.0.0.1', 5088

    def run_app():
        app.run(host=HOST, port=PORT, debug=False)
        time.sleep(.1)  # give it some time to start

    proc = multiprocessing.Process(target=run_app)
    proc.start()

    def cleanup():
        proc.terminate()
        proc.join()

    request.addfinalizer(cleanup)

    return RunningAppInfo(url='http://{0}:{1}'.format(HOST, PORT), app=app)
