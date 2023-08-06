import json
import os
import uuid
import flask

import conf


def help(signtype):
    return f"""
    {signtype.ljust(20, ' ')}sign a sub ca certificate.
                        req: certificate request file for sign
                        Ex: curl {conf.config['ListenHost']}/sign/{signtype} -F 'req=@<req file path>'"""
    
def checktype(cn):
    return json.loads(os.popen(f'openssl x509 -in pki/issued/{cn.lower()}.crt -text | grep -A 1 "Basic Constraints:" | grep "CA" | sed \'s/\s//g\' | awk -F \':\' \'{{print $2}}\'').read().strip().lower())

def sign():
    reqname = f'/tmp/{str(uuid.uuid4())}.req'
    flask.request.files['req'].save(reqname)
    subject = json.loads('{"' + os.popen(f'openssl req -in {reqname} -text | grep -oP \'(?<=Subject:).*\' | sed \'s/\s*=\s*/\":\"/g\' | sed \'s/,\s*/\",\"/g\'').read().strip() + '"}')

    ipindex = conf.getipindex(flask.request.remote_addr)
    if ipindex < 0:
        return "Invalid IP address.", 403
    userdata = conf.getuserinfo({"ipindex":ipindex})

    if subject['CN'].lower() != userdata['username']:
        return "Invalid CA common name. please use username.", 403
    elif os.path.isfile(f'pki/issued/{subject["CN"].lower()}.crt'):
        os.remove(reqname)
        return f"Common name: {subject['CN'].lower()} already exist. Please revoke old certificate first.", 403
    os.system(f'easyrsa --batch import-req {reqname} \'{subject["CN"].lower()}\'')
    os.system(f'easyrsa --batch sign-req ca \'{subject["CN"].lower()}\'')
    return 'Certificate sign success. Please use "downloadcert" api to download your certificate.'

def revoke(cn):
    ipindex = conf.getipindex(flask.request.remote_addr)
    if ipindex < 0:
        return "Invalid IP address.", 403
    userdata = conf.getuserinfo({"ipindex":ipindex})

    if cn != userdata['username']:
        return "Invalid CA common name. You only can control CN with your username.", 403

    os.system(f'easyrsa --batch revoke \'{cn}\'')
    os.system('easyrsa gen-crl')
    return 'Success'

