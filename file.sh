#!/bin/bash

# Cài đặt Chrome
apt-get update
apt-get install -y wget unzip xvfb libxi6 libgconf-2-4 libappindicator1 libnss3 libxss1 libasound2

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i google-chrome*.deb || apt-get -fy install

# Chạy ứng dụng
streamlit run app.py --server.port=$PORT --server.enableCORS=false
