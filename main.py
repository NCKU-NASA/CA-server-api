import os
import sys
import zipfile
import io
import flask
import importlib

import conf

signmodules = {}
for path in os.listdir("../sign"):
    if path.endswith(".py"):
        modulename = os.path.splitext(path)[0]
        signmodules[modulename] = importlib.import_module(f'sign.{modulename}')

app = flask.Flask(__name__)

@app.route('/',methods=['GET'])
@app.route('/help',methods=['GET'])
def help():
    return f"""
Usage: {conf.config['ListenHost']}/<api>

GET:
    ca                  download ca certificate.
                        Ex: wget {conf.config['ListenHost']}/ca -O rootca.crt
    crl                 download crl.
                        Ex: wget {conf.config['ListenHost']}/crl -O rootcrl.crl
    list                list all certificate CN.
                        Ex: curl {conf.config['ListenHost']}/list
    downloadcert/<CN>   download certificate.
                        Ex: wget {conf.config['ListenHost']}/downloadcert/<CN> -O certificate.zip
    username            get username.
                        Ex: curl {conf.config['ListenHost']}/username

DELETE:
    revoke/<CN>         revoke your certificate.
                        Ex: curl -X DELETE {conf.config['ListenHost']}/revoke/<CN>

route:
    sign                sign certificate.
                        use 'curl {conf.config['ListenHost']}/sign' to see usage
"""

@app.route('/ca',methods=['GET'])
def ca():
    return flask.send_file(os.path.abspath("pki/ca.crt"), mimetype='application/x-x509-ca-cert',as_attachment=True,attachment_filename='ca.crt')

@app.route('/crl',methods=['GET'])
def crl():
    if os.path.isfile('pki/crl.pem'):
        os.system('./easyrsa gen-crl')
    return flask.send_file(os.path.abspath("pki/crl.pem"), mimetype='application/x-pkcs7-crl',as_attachment=True,attachment_filename='crl.crl')

@app.route('/downloadcert/<cn>',methods=['GET'])
def downloadcert(cn):
    certpath = f'pki/issued/{cn.lower()}.crt'
    if os.path.isfile(certpath):
        outfile = io.BytesIO()
        with zipfile.ZipFile(outfile, mode='w') as z:
            z.write(certpath,arcname='certificate.crt')
            z.write('pki/ca.crt',arcname='chain.crt')
            with open(certpath, 'r') as f:
                certdata = f.read()
            with open('pki/ca.crt', 'r') as f:
                chaindata = f.read()
            z.writestr('fullchain.crt', certdata + '\n' + chaindata)
        outfile.seek(0)

        return flask.send_file(outfile,mimetype='application/zip',as_attachment=True,attachment_filename='certificate.zip')
    else:
        return "Certificate nonexist.", 403

@app.route('/list',methods=['GET'])
def listcert():
    return '\n'.join([os.path.splitext(path)[0] for path in os.listdir("pki/issued")])

@app.route('/username',methods=['GET'])
def getusername():
    ipindex = conf.getipindex(flask.request.remote_addr)
    if ipindex < 0:
        return "Invalid IP address.", 403
    return conf.getuserinfo({"ipindex":ipindex})['username']

@app.route('/sign',methods=['GET'])
def signhelp():
    methodhelp = '\n'.join([signmodules[signtype].help(signtype) for signtype in signmodules])
    return f"""
Usage: {conf.config['ListenHost']}/sign/<api>

POST:
{methodhelp}
"""

@app.route('/sign/<certtype>',methods=['POST'])
def sign(certtype):
    if certtype not in signmodules:
        return "Invalid type.", 403
    return signmodules[certtype].sign()


@app.route('/revoke/<cn>',methods=['DELETE'])
def revoke(cn):
    #certpath = f'pki/issued/{cn.lower()}.crt'
    if os.path.isfile(f'pki/issued/{cn.lower()}.crt'):
        for signtype in signmodules:
            if signmodules[signtype].checktype(cn):
                return signmodules[signtype].revoke(cn)

        return "Revoke bad certificate type.", 403
    else:
        return "Certificate nonexist.", 403
        os.system(f'./easyrsa --batch revoke \'{cn}\'')
        os.system('./easyrsa gen-crl')

@app.errorhandler(404)
def page_not_found(e):
    return_result = {'code': 404, 'Success': False,
                     "Message": "The website is not available currently"}
    return flask.jsonify(return_result), 404


@app.errorhandler(403)
def forbidden(e):
    return_result = {'code': 403, 'Success': False,
                     "Message": "The website is not available currently"}
    return flask.jsonify(return_result), 403

if __name__ == "__main__":
    app.run(host=conf.config['ListenHost'],port=conf.config['ListenPort'])
