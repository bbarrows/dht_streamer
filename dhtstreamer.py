from dht_tornado import dht
from functools import partial
import sys, re, random, thread, threading, os, re
import logging, json

import tornado.ioloop
from tornado import iostream
import tornado.options
from tornado.options import define, options
import tornado.web
import tornado.httpserver

class IndexHandler(tornado.web.RequestHandler):
    @classmethod
    def register_dht(self, dht):
        self.dht = dht

    def get(self):
        self.write( "Hello" )


if __name__ == "__main__":
    io_loop = tornado.ioloop.IOLoop()
    io_loop.install()

    define('debug',default=True, type=bool) # save file causes autoreload
    define('frontend_port',default=7070, type=int)
    
    tornado.options.parse_command_line()
    settings = dict( (k, v.value()) for k,v in options.items() )

    ip_ports =  [('202.177.254.130', 43251), ('71.7.233.108', 40641), ('189.223.55.147', 54037), ('186.213.54.11', 57479), ('85.245.177.29', 58042), ('2.81.68.199', 37263), ('188.24.193.27', 15796), ('210.252.33.4', 39118), ('175.143.215.38', 56067), ('95.42.100.15', 34278), ('211.224.26.47', 25628), ('92.6.154.240', 48783), ('173.255.163.104', 52159), ('2.10.206.61', 12815), ('187.123.98.253', 58901), ('83.134.13.212', 10770), ('78.139.207.123', 50045), ('125.25.191.209', 56548), ('71.234.82.146', 14973), ('72.207.74.219', 14884), ('79.136.190.188', 50634), ('72.80.103.198', 36823), ('77.122.72.44', 56554)]

    dht = dht.DHT(51414, ip_ports, io_loop = io_loop)
    dht.start()
    
    frontend_routes = [
        ('/?', IndexHandler),
    ]
    frontend_application = tornado.web.Application(frontend_routes, **settings)
    frontend_server = tornado.httpserver.HTTPServer(frontend_application, io_loop=io_loop)
    frontend_server.bind(options.frontend_port, '')
    frontend_server.start()    

    IndexHandler.register_dht(dht)
    
    


