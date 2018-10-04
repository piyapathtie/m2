import os
import json
import redis
from flask import Flask, jsonify, request
import logging
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
LOG = logging

LOG.basicConfig(
    level=LOG.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class RedisResource:
    REDIS_QUEUE_LOCATION = os.getenv('REDIS_QUEUE', 'localhost')
    QUEUE_NAME = 'queue:factoring'

    host, *port_info = REDIS_QUEUE_LOCATION.split(':')
    port = tuple()
    if port_info:
        port, *_ = port_info
        port = (int(port),)

    conn = redis.Redis(host=host, *port)

@app.route('/factor', methods=['POST'])
def post_factor_job():
    body = request.json
    json_packed = json.dumps(body)
    # LOG.info(json_packed)
    # LOG.info('http://sos:8080/{}/{}'.format(bucketname, objectname))
    # resp = requests.get('http://sos:8080/{}/{}'.format(bucketname, objectname))
    # newFile = open( "../worker/data/" + objectname + ".mp4", "wb")
    # newFile.write(resp.content)

    LOG.info("packed: %s", json_packed)
    RedisResource.conn.rpush(
        RedisResource.QUEUE_NAME,
        json_packed)

    return jsonify({'status': 'OK'})

    

