import yaml
import json
import requests

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

def getipindex(ipaddr):
    for net in config['AllowNetworks']:
        if ipaddress.ip_address(ipaddr) in ipaddress.ip_network(net):
            return list(ipaddress.ip_network(net)).index(ipaddress.ip_address(ipaddr))
    return -1

def getuserinfo(jsondata):
    return requests.post(f'{config["JudgeAPIURL"]}/user/getdata', json=jsondata).json()

