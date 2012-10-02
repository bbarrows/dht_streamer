from dht_tornado import dht
from dht_bootstrapper import bht
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

def let_the_streaming_begin(io_loop, bootstrap_ip_ports):
    dht = dht.DHT(51414, bootstrap_ip_ports, io_loop = io_loop)
    dht.start()

    Client.resume()
    client = Client.instances[0]
    
    frontend_routes = [
        ('/?', IndexHandler),
    ]
    frontend_application = tornado.web.Application(frontend_routes, **settings)
    frontend_server = tornado.httpserver.HTTPServer(frontend_application, io_loop=io_loop)
    frontend_server.bind(options.frontend_port, '')
    frontend_server.start()    

    IndexHandler.register_dht(dht)


if __name__ == "__main__":
    io_loop = tornado.ioloop.IOLoop()
    io_loop.install()

    define('debug',default=True, type=bool) # save file causes autoreload
    define('frontend_port',default=7070, type=int)
    define('bootstrap',default="", type=str)
    define('bootstrap_torrent',default="", type=str)

    tornado.options.parse_command_line()

    #Startup the dht with some bootstrap ports
    bootstrap_ip_ports = []
    for ip_port in options.bootstrap.split(","):
        bootstrap_ip_ports.append(ip_port.split(':'))

    if len(bootstrap_ip_ports) == 0:
        bht.get_dht_peers_from_torrent(options.bootstrap_torrent or "bootstrap.torrent", partial(let_the_streaming_begin, io_loop))
    else:
        let_the_streaming_begin(io_loop, bootstrap_ip_ports)
    
    


