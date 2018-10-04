#!/usr/bin/env python3
import os
import logging
import json
import uuid
import redis
import requests
import subprocess

import time
import hashlib


LOG = logging
REDIS_QUEUE_LOCATION = os.getenv('REDIS_QUEUE', 'localhost')
QUEUE_NAME = 'queue:factoring'

INSTANCE_NAME = uuid.uuid4().hex

LOG.basicConfig(
    level=LOG.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def watch_queue(redis_conn, queue_name, callback_func, timeout=30):
    active = True

    while active:
        # Fetch a json-encoded task using a blocking (left) pop
        packed = redis_conn.blpop([queue_name], timeout=timeout)

        if not packed:
            # if nothing is returned, poll a again
            continue

        _, packed_task = packed

        # If it's treated to a poison pill, quit the loop
        if packed_task == b'DIE':
            active = False
        else:
            task = None
            try:
                task = json.loads(packed_task.decode('utf8'))
            except Exception:
                LOG.exception('json.loads failed')
            if task:
                callback_func(task)

def execute_factor(log, task):
    log.info("hereeee")
    bucketname = task.get("bucketname")
    objectname = task.get("objectname")
    targetbucket = task.get("targetbucket")
    targetobject = task.get("targetobject")
    os.mkdir("./data/"+INSTANCE_NAME)
    resp = requests.get('http://sos:8080/{}/{}'.format(bucketname, objectname))
    newFile = open( "./data/" + INSTANCE_NAME + "/" + objectname + ".mp4", "wb")
    newFile.write(resp.content)
    newFile.close()
    subprocess.call(["./make_thumbnail", INSTANCE_NAME + "/" + objectname+".mp4", INSTANCE_NAME + "/" + targetobject+".gif"])

    # time.sleep(20)

    resp2 = requests.post(url='http://sos:8080/{}/{}?create'.format(targetbucket, targetobject))

    data = open('./data/{}/{}.gif'.format(INSTANCE_NAME, targetobject), 'rb').read()
	
    resp3 = requests.put(url='http://sos:8080/{}/{}?partNumber=1'.format(targetbucket, targetobject), data=data, headers={'Content-Length': str(len(data)), 'Content-MD5': hashlib.md5(data).hexdigest(), 'Extension': "gif"})

    # number = task.get('number')
    # if number:
    #     number = int(number)
    #     log.info('Factoring %d', number)
    #     factors = [trial for trial in range(1, number+1) if number % trial == 0] 
    #     log.info('Done, factors = %s', factors)

    # else:
    #     log.info('No number given.')
        

def main():
    LOG.info('Starting a worker...')
    LOG.info('Unique name: %s', INSTANCE_NAME)
    host, *port_info = REDIS_QUEUE_LOCATION.split(':')
    port = tuple()
    if port_info:
        port, *_ = port_info
        port = (int(port),)

    named_logging = LOG.getLogger(name=INSTANCE_NAME)
    named_logging.info('Trying to connect to %s [%s]', host, REDIS_QUEUE_LOCATION)
    redis_conn = redis.Redis(host=host, *port)
    watch_queue(
        redis_conn, 
        QUEUE_NAME, 
        lambda task_descr: execute_factor(named_logging, task_descr))

if __name__ == '__main__':
    main()
