# _*_ coding:utf-8 _*_
"""
数据控制
"""
import threading
import time
import json
import docker
from elasticsearch import Elasticsearch

with open("D:\\APM\\Code\\xuyp\\docker\\docker_monitor\\config.json", "r") as files:
    CONFIG = json.load(files)
ES_URL = "{url}:{port}".format(url=CONFIG["es_ip"], port=CONFIG["es_port"])
DOCKER_URL = "{url}:{port}".format(url=CONFIG["docker_ip"], port=CONFIG["docker_port"])

global threads
threads = []

ES = Elasticsearch([ES_URL])

def cpu(data):
    return (
        data["cpu_stats"]["cpu_usage"]["total_usage"],
        data["cpu_stats"]["system_cpu_usage"],
        data["cpu_stats"]["cpu_usage"]["percpu_usage"],
        data["memory_stats"]["usage"],
        data["memory_stats"]["limit"],
        data["networks"]["eth0"]["rx_bytes"]/1024/1024.0,
        data["networks"]["eth0"]["tx_bytes"]/1024/1024.0
    )
def cpu_usages(
        cpu_total_usage, pre_cpu_total_usage, system_usage,
        pre_system_usage, per_cpu_usage_array
    ):
    cpu_delta = float(cpu_total_usage - pre_cpu_total_usage)
    system_delta = system_usage - pre_system_usage
    cpu_usage = ((cpu_delta / system_delta) * len(per_cpu_usage_array)) * 100.0
    return cpu_usage

def stats(container):
    gen = container.stats(decode=True, stream=True)
    data_pre = cpu(next(gen))
    pre_cpu_total_usage, pre_system_usage = data_pre[:2]
    data_next = cpu(next(gen))
    cpu_total_usage, system_usage, per_cpu_usage_array = data_next[:3]
    cpu_usage = cpu_usages(
        cpu_total_usage, pre_cpu_total_usage, system_usage,
        pre_system_usage, per_cpu_usage_array
    )
    mem_percent = float(data_next[3])/data_next[4] * 100
    net_input = data_next[5] - data_pre[5]
    net_output = data_next[6] - data_pre[6]
    response = {
        "container": container.name,
        "cpu": round(cpu_usage, 2),
        "mem": round(mem_percent, 2),
        "input": round(net_input, 2),
        "output": round(net_output, 2),
        "timestamp": long(time.time() * 1000)
    }
    ES.index(index='docker', doc_type=response["container"], body=json.dumps(response))


def docker_perf(url='tcp://{url}'.format(url=DOCKER_URL)):
    """
    get all the containers object and use muti-thread to excute tasks

    """
    client = docker.DockerClient(base_url=url)

    for container in client.containers.list():
        threads.append(MULTI(stats, args=container))

    for task in threads:
        task.start()

def pause():
    for active_thread in threads:
        active_thread.pause()
    return long(time.time() * 1000)

def resume():
    for active_thread in threads:
        active_thread.resume()
    return long(time.time() * 1000)

def stop():
    for active_thread in threads:
        active_thread.stop()
    return long(time.time() * 1000)


class MULTI(threading.Thread):
    def __init__(self, func, args):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        self.__flag = threading.Event()
        self.__flag.set()
        self.__running = threading.Event()
        self.__running.set()

    def run(self):
        while self.__running.isSet():
            self.__flag.wait()
            self.func(self.args)

    def pause(self):
        self.__flag.clear()

    def resume(self):
        self.__flag.set()

    def stop(self):
        self.__flag.set()
        self.__running.clear()
