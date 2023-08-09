FROM debian:latest

ARG CACN=testca

WORKDIR /usr/app
COPY . .
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y lsb-release procps git curl wget gnupg2 iputils-ping mtr dnsutils python3 python3-venv  python3-dev python3-pip
RUN git clone https://github.com/OpenVPN/easy-rsa && \
    mv easy-rsa/easyrsa3 /usr/local/share/easy-rsa && \
    ln -s ../share/easy-rsa/easyrsa /usr/local/bin/easyrsa
RUN easyrsa init-pki && \
    echo "nsc39" | easyrsa build-ca nopass && \
    easyrsa gen-crl
RUN wget https://github.com/mikefarah/yq/releases/download/v4.17.2/yq_linux_$(dpkg --print-architecture).tar.gz -O - | tar xz && mv yq_linux_$(dpkg --print-architecture) /usr/bin/yq
RUN pip3 install -r requirements.txt --break-system-packages
RUN echo "#!/bin/bash" > /usr/local/bin/caserverapi && \
    echo "cd /usr/app" >> /usr/local/bin/caserverapi && \
    sed '/^[ \t]*$/d' caserverapi.sh | tail -n 1 >> /usr/local/bin/caserverapi && \
    chmod +x /usr/local/bin/caserverapi



