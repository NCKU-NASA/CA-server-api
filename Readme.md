# CA-server-api

## install
1. Clone repo
``` bash
git clone https://github.com/NCKU-NASA/CA-server-api
cd CA-server-api
```

2. Run install.sh
``` bash
bash install.sh
```

3. Set config
``` bash
vi /etc/caserverapi/config.yaml
```

4. Write your challenge code under `sign`
```
# for example
ls /etc/caserverapi/sign
```

6. Start service
```bash
systemctl start caserverapi
```
