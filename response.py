import time

from flask import jsonify


def success(result=None):
    return jsonify(success=True,
                   result=result,
                   server_clock=int(time.time())), 200


def error(message=None):
    return jsonify(success=False,
                   result={'message': message},
                   server_clock=int(time.time())), 400
