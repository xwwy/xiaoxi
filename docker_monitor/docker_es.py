# _*_ coding: utf-8 _*_
"""
get data from es

"""
import json
import docker
from elasticsearch import Elasticsearch, RequestError

with open("D:\\APM\\Code\\xuyp\\docker\\docker_monitor\\config.json", "r") as files:
    CONFIG = json.load(files)
ES_URL = "{url}:{port}".format(url=CONFIG["es_ip"], port=CONFIG["es_port"])
DOCKER_URL = "{url}:{port}".format(url=CONFIG["docker_ip"], port=CONFIG["docker_port"])

CLIENT = docker.DockerClient(base_url='tcp://{url}'.format(url=DOCKER_URL))
ES = Elasticsearch([ES_URL])
MAP_SET = {
    "mappings": {
        "docker" : {
            "properties":{
                "container": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "cpu": {
                    "type": "float"
                },
                "mem": {
                    "type": "float"
                },
                "input": {
                    "type": "float"
                },
                "output": {
                    "type": "float"
                },
                "timestamp": {
                    "type": "long"
                }
            }
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas" : 1
        },
    "template": "docker"
}
try:
    ES.indices.create(index="docker", body=MAP_SET)
except RequestError, argument:
    print argument

def perf_data(start_date, end_date, docker_name):
    """
    get performance data from docker_name

    """
    data = []
    query = {
        "query":{
            "bool": {
                "filter": [
                    {
                        "term": {
                            "container": docker_name
                        }
                    },
                    {
                        "range": {
                            "timestamp": {
                                "gte": long(start_date),
                                "lt": long(end_date)
                            }
                        }
                    }
                ]
            }
        },
        "sort": [
            {
                "timestamp": {
                    "order": "asc"
                    }
                }
            ]
        }

    size = (ES.search(index="docker", body=query))["hits"]["total"]
    query["size"] = size
    rawdata = ES.search(index="docker", body=query)
    for source in rawdata["hits"]["hits"]:
        data.append(source["_source"])
    return {
        "name": docker_name,
        "performance": data
    }

def performance(start_date, end_date):
    """
    return all the container's data

    """
    multidata = []
    for container in CLIENT.containers.list():
        multidata.append(perf_data(start_date, end_date, container.name))
    result = {
        "result": multidata
    }
    return json.dumps(result)


def average(start_date, end_date):
    """
    get the average data

    """
    query = {
        "size": 0,
        "query": {
            "bool": {
                "filter": {
                    "range": {
                        "timestamp": {
                            "gte": start_date,
                            "lt": end_date
                            }
                        }
                    }
                }
            },
        "aggs": {
            "average": {
                "terms": {
                    "field": "container",
                    "size": 0
                    },
                "aggs": {
                    "avg_cpu": {
                        "avg": {
                            "field": "cpu"
                        }
                    },
                    "avg_mem": {
                        "avg": {
                            "field": "mem"
                        }
                    },
                    "avg_input": {
                        "avg": {
                            "field": "input"
                        }
                    },
                    "avg_output": {
                        "avg": {
                            "field": "output"
                        }
                    }
                }
            }
        }
    }
    avera = []
    rawdata = ES.search(index="docker", body=query)['aggregations']['average']['buckets']
    for data in rawdata:
        aver = {
            "name": data["key"],
            "performace": {
                'avg_cpu': round(data['avg_cpu']['value'], 2),
                'avg_mem': round(data['avg_mem']['value'], 2),
                'avg_input': round(data['avg_input']['value'], 2),
                'avg_output': round(data['avg_output']['value'], 2)
            }
        }
        avera.append(aver)
    result_avg = {
        "result": avera
    }
    return json.dumps(result_avg)
