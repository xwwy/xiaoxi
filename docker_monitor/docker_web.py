# _*_ coding:utf-8 _*_

import time
import json
import docker_data as da
import docker_es as ds
from flask import Flask, request, url_for

APP = Flask(__name__)
START_TIME = long(time.time() * 1000)
STATUS = "stop"

@APP.route('/', methods=['GET'])
def index():
    return url_for('static', filename='index.html')

@APP.route('/static/web/time', methods=['GET'])
def now():
    now_time = {
        "timestamp": long(time.time() * 1000)
    }
    return json.dumps(now_time)

@APP.route('/static/web/dockers', methods=['GET'])
def get_names():
    """
    return all the docker containers

    """
    contain = []

    for container in ds.CLIENT.containers.list():
        contain.append(container.name)
    dockers = {
        "dockers": contain,
        "status": STATUS
    }
    return json.dumps(dockers)

@APP.route('/static/web/perf', methods=['GET'])
def performance():
    """
    return all the containers data

    """
    start_date = long(request.args.get('start_date'))
    end_date = long(request.args.get('end_date'))
    start_date = start_date if start_date > START_TIME else START_TIME
    result = ds.performance(start_date, end_date)
    return result

@APP.route('/static/web/start', methods=['put'])
def start_storage():
    """
    start collect performaces data

    """
    if not da.threads:
        da.docker_perf()
        result = {
            "result": "success",
            "status": "start",
            "timestamp": long(time.time() * 1000)
        }
    else:
        timestamp = da.resume()
        result = {
            "result": "success",
            "status": "start",
            "timestamp": timestamp
        }
    global START_TIME
    global STATUS
    START_TIME = long(time.time() * 1000)
    STATUS = "start"
    return json.dumps(result)

@APP.route('/static/web/average', methods=['GET'])
def average():
    """
    get the average data

    """
    start_date = START_TIME
    end_date = request.args.get('end_date')
    result_avg = ds.average(start_date, end_date)
    return result_avg


@APP.route('/static/web/stop', methods=['PUT'])
def stop():
    timestamp = da.pause()
    result = {
        "result": "success",
        "status": "stop",
        "timestamp": timestamp
    }
    global STATUS
    STATUS = "stop"
    return json.dumps(result)


if __name__ == '__main__':
    APP.run(host='0.0.0.0', port=88)
