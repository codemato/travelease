#!/bin/bash
export PATH=$PATH:/home/ubuntu/travelease/travelease/bin
cd /home/ubuntu/travelease/travelease
kill -9 $(netstat -tulpn | grep -i python | grep -i 0.0.0.0:80 | awk  '{print $7}' | sed 's/\/python//g')
git stash
git pull
nohup streamlit run app.py --server.port 80 &
echo "done"
