import json
import os
import uuid
import dns.resolver
import re
import flask

import conf

def help(signtype):
    return f"""
    {signtype.ljust(20, ' ')}sign a web certificate.
                        req: certificate request file for sign
                        Ex: curl {conf.config['ListenHost']}/sign/{signtype} -F 'req=@<req file path>'"""
    
def checktype(cn):
    return not json.loads(os.popen(f'openssl x509 -in pki/issued/{cn.lower()}.crt -text | grep -A 1 "Basic Constraints:" | grep "CA" | sed \'s/\s//g\' | awk -F \':\' \'{{print $2}}\'').read().strip().lower())

def sign():
    reqname = f'/tmp/{str(uuid.uuid4())}.req'
    flask.request.files['req'].save(reqname)
    subject = json.loads('{"' + os.popen(f'openssl req -in {reqname} -text | grep -oP \'(?<=Subject:).*\' | sed \'s/\s*=\s*/\":\"/g\' | sed \'s/,\s*/\",\"/g\'').read().strip() + '"}')
    subaltname = os.popen(f'openssl req -in {reqname} -text | grep -A 1 \'Subject Alternative Name:\' | tail -n 1 | sed \'s/\s//g\'').read().strip().split(',')
    if os.path.isfile(f'pki/issued/{subject["CN"].lower()}.crt'):
        os.remove(reqname)
        return f"Common name: {subject['CN'].lower()} already exist. Please revoke old certificate first.", 403
    for name in subaltname:
        if name == '':
            os.remove(reqname)
            return "Invalid Subject Alternative Name. Please use an existing DNS A record.", 403
        elif name[:3] != "DNS":
            os.remove(reqname)
            return "Invalid Subject Alternative Name. We only valid DNS Subject Alternative Name.", 403
        try:
            if len(dns.resolver.query(re.sub(r'DNS:[^.]*\.', '', name),'NS')) < 1:
                os.remove(reqname)
                return "Invalid Subject Alternative Name. Nonexistent NS record.", 403
            elif conf.getipindex(flask.request.remote_addr) < 0:
                return "Invalid IP address.", 403
            elif conf.getipindex(str(dns.resolver.resolve(str(dns.resolver.resolve(re.sub(r'DNS:[^.]*\.', '', name),'NS')[0]), 'A')[0])) != conf.getipindex(flask.request.remote_addr):
                os.remove(reqname)
                return "Invalid Subject Alternative Name. You only can use your own DNS zone.", 403
            elif name != 'DNS:*.'+re.sub(r'DNS:[^.]*\.', '', name):
                if len(dns.resolver.resolve(re.sub(r'DNS:', '', name),'A')) < 1:
                    os.remove(reqname)
                    return "Invalid Subject Alternative Name. Nonexistent A record.", 403
        except:
            os.remove(reqname)
            return "Invalid Subject Alternative Name. Nonexistent record.", 403

    os.system(f'easyrsa --batch import-req {reqname} \'{subject["CN"].lower()}\'')
    os.system(f'easyrsa --copy-ext --batch sign-req server \'{subject["CN"].lower()}\'')
    return 'Certificate sign success. Please use "downloadcert" api to download your certificate.'

def revoke(cn):
    subaltname = os.popen('openssl x509 -in {certpath} -text | grep -A 1 \'Subject Alternative Name:\' | tail -n 1 | sed \'s/\s//g\'').read().strip().split(',')
    for name in subaltname:
        if name == '':
            return "Invalid Subject Alternative Name. You only can use your own DNS zone.", 403
        elif conf.getipindex(flask.request.remote_addr) < 0:
            return "Invalid IP address.", 403
        elif conf.getipindex(str(dns.resolver.resolve(str(dns.resolver.resolve(re.sub(r'DNS:[^.]*\.', '', name),'NS')[0]), 'A')[0])) != conf.getipindex(flask.request.remote_addr):
            return "Invalid Subject Alternative Name. You only can use your own DNS zone.", 403

    os.system(f'easyrsa --batch revoke \'{cn}\'')
    os.system('easyrsa gen-crl')
    return 'Success'

