import hmac
import hashlib
from trading_config_loader import API_SECRET
import json

MAX_LEVEL = 3

def params_to_str(obj, level):
    if level >= MAX_LEVEL:
        return str(obj)

    return_str = ""
    for key in sorted(obj):
        return_str += key
        if obj[key] is None:
            return_str += 'null'
        elif isinstance(obj[key], list):
            for subObj in obj[key]:
                return_str += params_to_str(subObj, ++level)
        else:
            return_str += str(obj[key])
    return return_str


def generate_api_signature(req):
    # First ensure the params are alphabetically sorted by key
    param_str = ""

    if "params" in req:
        param_str = params_to_str(req['params'], 0)

    payload_str = req['method'] + \
        str(req['id']) + req['api_key'] + param_str + str(req['nonce'])

    req['sig'] = hmac.new(
        bytes(str(API_SECRET), 'utf-8'),
        msg=bytes(payload_str, 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    return json.dumps(req)
