dht_streamer
============

To setup:
git submodule init
git submodule update

cd dht_bootstrapper; git checkout master; git pull; cd ..

cd dht_tornado; git checkout master; git pull; cd ..

cd ktorrent; git checkout master; git pull; cd ..

cd tornado; git checkout master; git pull; cd ..

easy_install virtualenv
virtualenv _install
source _install/bin/activate

ln -s _install/lib/python2.7/site-packages/
cd _install/lib/python2.7/site-packages/;  ln -s ../../../../tornado/tornado/ tornado

easy_install bencode
To run:

PYTHONPATH=ktorrent/ python dhtstreamer.py

One project, a few repos, and hopefully an awesome way to stream video from popular torrents.