import os
import json
import uuid
import base64
import zipfile
import io
import re
import dns.resolver

from flask import Flask,request,redirect,Response,make_response,jsonify,render_template,session,send_file

app = Flask(__name__)

@app.route('/',methods=['GET'])
@app.route('/help',methods=['GET'])
def help():
    return """
Usage: rootca.nasa/<api>

GET:
    ca              download ca certificate.
                    Ex: wget rootca.nasa/ca -O rootca.crt
    crl             download crl.
                    Ex: wget rootca.nasa/crl -O rootcrl.crl

POST:
    sign            sign certificate.
                    Options:
                        type: your certificate type. Ex: ca, web
                        req: your req file(encode with base64).
                    Ex: wget rootca.nasa/sign --header 'Content-Type:application/json' --post-data '{\"type\":\"ca\",\"req\":\"$(cat <req file> | base64)\"}' -O certificate.zip
    downloadcert    download certificate.
                    Options:
                        CN: your certificate CN.
                    Ex: wget rootca.nasa/downloadcert --header 'Content-Type:application/json' --data '{\"CN\":\"<CN>\"}' -O certificate.zip
    revoke          revoke your certificate.
                    Options:
                        CN: your certificate CN.
                    Ex: curl -X POST rootca.nasa/revoke -H 'Content-Type:application/json' --data '{\"CN\":\"<CN>\"}'
"""

@app.route('/ca',methods=['GET'])
def ca():
    with open("easy-rsa/pki/ca.crt", 'r') as f:
        data=f.read()
    return data

@app.route('/crl',methods=['GET'])
def crl():
    with open("easy-rsa/pki/crl.pem", 'r') as f:
        data=f.read()
    return data

@app.route('/sign',methods=['POST'])
def sign():
    data = json.loads(request.get_data())
    reqname = '/tmp/' + str(uuid.uuid4()) + '.req'
    with open(reqname, 'wb') as f:
        f.write(base64.b64decode(data['req'].encode("UTF-8")))
    subject = json.loads('{"' + os.popen('openssl req -in ' + reqname + ' -text | grep -oP \'(?<=Subject:).*\' | sed \'s/\s*=\s*/\":\"/g\' | sed \'s/,\s*/\",\"/g\'').read().strip() + '"}')
    if data['type'] == 'ca':
        studentid=os.popen('curl -X POST 10.31.31.254/studentidtoip -H \'Content-Type:application/json\' --data \'{"ip":"' + request.remote_addr + '"}\'').read().strip().lower()
        if subject['CN'].lower() != studentid:
            return "Invalid CA common name. please use studentid."

        os.system('./easyrsa import-req ' + reqname + ' \'' + subject['CN'].lower() + '\' --batch')
        os.system('./easyrsa sign-req ca \'' + subject['CN'].lower() + '\' --batch')
    elif data['type'] == 'web':
        subaltname = os.popen('openssl req -in ' + reqname + ' -text | grep -A 1 \'Subject Alternative Name:\' | tail -n 1 | sed \'s/\s//g\'').read().strip().split(',')
        for name in subaltname:
            if name == '':
                return "Invalid Subject Alternative Name. Please use an existing DNS A record."
            elif name[:3] != "DNS":
                return "Invalid Subject Alternative Name. We only valid DNS Subject Alternative Name."
            elif len(dns.resolver.query(re.sub(r'DNS:[^.]*\.', '', name),'NS')) < 1:
                return "Invalid Subject Alternative Name. Nonexistent NS record."
            elif str(dns.resolver.resolve(str(dns.resolver.resolve(re.sub(r'DNS:[^.]*\.', '', name),'NS')[0]), 'A')[0]) != request.remote_addr:
                return "Invalid Subject Alternative Name. You only can use your own DNS zone."
            elif name != 'DNS:*.'+re.sub(r'DNS:[^.]*\.', '', name):
                try:
                    if len(dns.resolver.resolve(re.sub(r'DNS:', '', name),'A')) < 1:
                        return "Invalid Subject Alternative Name. Nonexistent A record."
                except:
                    return "Invalid Subject Alternative Name. Nonexistent A record."

        os.system('./easyrsa import-req ' + reqname + ' \'' + subject['CN'].lower() + '\' --batch')
        os.system('./easyrsa sign-req server \'' + subject['CN'].lower() + '\' --copy-ext --batch')
    else:
        return "Invalid type."

    return downloadcert(justsign=True,cn=subject['CN'].lower())


@app.route('/downloadcert',methods=['POST'])
def downloadcert(justsign=False,cn=''):
    if justsign:
        subject = {'CN':cn}
    else:
        subject = json.loads(request.get_data())

    if os.path.isfile('pki/issued/' + subject['CN'].lower() + '.crt'):
        outfile = io.BytesIO()
        with zipfile.ZipFile(outfile, mode='w') as z:
            z.write('pki/issued/' + subject['CN'].lower() + '.crt',arcname='certificate.crt')
            z.write('pki/ca.crt',arcname='chain.crt')
            with open('pki/issued/' + subject['CN'].lower() + '.crt', 'r') as f:
                certdata = f.read()
            with open('pki/ca.crt', 'r') as f:
                chaindata = f.read()
            z.writestr('fullchain.crt', certdata + '\n' + chaindata)
        outfile.seek(0)

        return send_file(outfile,mimetype='application/zip',as_attachment=True,attachment_filename='certificate.zip')
    else:
        return "Certificate nonexist."

@app.route('/revoke',methods=['POST'])
def revoke():
    subject = json.loads(request.get_data())
    if os.path.isfile('pki/issued/' + subject['CN'].lower() + '.crt'):
        isca = json.loads(os.popen('openssl x509 -in pki/issued/' + subject['CN'].lower() + '.crt -text | grep -A 1 "Basic Constraints:" | grep "CA" | sed \'s/\s//g\' | awk -F \':\' \'{print $2}\'').read().strip())
        if isca:
            studentid=os.popen('curl -X POST 10.31.31.254/studentidtoip -H \'Content-Type:application/json\' --data \'{"ip":"' + request.remote_addr + '"}\'').read().strip().lower()
            if subject['CN'].lower() != studentid:
                return "Invalid CA common name. You only can control CN with your studentid."
        else:
            subaltname = os.popen('openssl x509 -in pki/issued/' + subject['CN'].lower() + '.crt -text | grep -A 1 \'Subject Alternative Name:\' | tail -n 1 | sed \'s/\s//g\'').read().strip().split(',')
            for name in subaltname:
                if name == '':
                    return "Invalid Subject Alternative Name. You only can use your own DNS zone."
                elif str(dns.resolver.resolve(str(dns.resolver.resolve(re.sub(r'DNS:[^.]*\.', '', name),'NS')[0]), 'A')[0]) != request.remote_addr:
                    return "Invalid Subject Alternative Name. You only can use your own DNS zone."
    else:
        return "Certificate nonexist."

    os.system('./easyrsa revoke \'' + subject['CN'].lower() + '\' --batch')
    os.system('./easyrsa gen-crl')
    return 'Success'

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=80)
