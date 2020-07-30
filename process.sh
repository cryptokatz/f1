#!/bin/sh
# This is a comment!
cd /var/www/html/
python getFeeds.py >temp.html
cp temp.html index.html
