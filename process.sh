#!/bin/sh
# This is a comment!
cd /var/www/html/f1/
python getFeeds.py >temp.html
cp temp.html index.html
