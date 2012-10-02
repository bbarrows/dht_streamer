from dht_tornado.dht import DHT
from dht_bootstrapper import bht
from functools import partial
import sys, re, random, thread, threading, os, re
import logging, json, signal

import tornado.ioloop
from tornado import iostream
import tornado.options
from tornado.options import define, options
import tornado.web
import tornado.httpserver
from tornado import httpclient

from ktorrent.frontend import IndexHandler, StatusHandler, APIHandler, PingHandler, VersionHandler, BtappHandler, PairHandler, request_logger, ProxyHandler, WebSocketProtocolHandler, GUIHandler, WebSocketProxyHandler, WebSocketIncomingProxyHandler, WebSocketUDPProxyHandler

from ktorrent.handlers import BitmaskHandler,\
    UTHandler,\
    NullHandler,\
    HaveHandler,\
    ChokeHandler,\
    InterestedHandler,\
    PortHandler,\
    UnChokeHandler,\
    NotInterestedHandler,\
    RequestHandler,\
    CancelHandler,\
    PieceHandler,\
    HaveAllHandler

home = os.getenv("HOME")

define('debug',default=True, type=bool) # save file causes autoreload
define('bootstrap',default="", type=str)
define('bootstrap_torrent',default="", type=str)

define('asserts',default=True, type=bool)
define('verbose',default=1, type=int)
define('host',default='10.10.90.24', type=str)

define('port',default=8030, type=int)
define('frontend_port',default=10000, type=int)
define('datapath',default=os.path.join(home,'ktorrent/data'), type=str)
define('static_path',default=os.path.join(home,'ktorrent/static'), type=str)
define('resume_file',default=os.path.join(home,'ktorrent/resume.dat'), type=str)
define('template_path',default=os.path.join(home,'ktorrent/templates'), type=str)

define('tracker_proxy',default='http://127.0.0.1:6969', type=str)

define('startup_connect_to', default='', type=str)
define('startup_connect_torrent', default='', type=str)
define('startup_connect_to_hash', default='', type=str)
define('startup_exit_on_close', default=False, help='quit program when connection closes', type=bool)

#define('outbound_piece_limit',default=1, type=int)
define('outbound_piece_limit',default=20, type=int)
define('piece_request_timeout',default=10, type=int)


frontend_routes = [
    ('/?', IndexHandler),
    ('/static/.?', tornado.web.StaticFileHandler),
    ('/gui/pingimg', PingHandler),
    ('/gui/pair/?', PairHandler),
    ('/gui/?', GUIHandler),
    ('/proxy/?', ProxyHandler),
    ('/version/?', VersionHandler),
    ('/statusv2/?', StatusHandler),
    ('/wsclient/?', WebSocketProtocolHandler),
    ('/wsproxy/?', WebSocketProxyHandler),
    ('/wsincomingproxy/?', WebSocketIncomingProxyHandler),
#    ('/wstrackerproxy/?', WebSocketTrackerProxyHandler),
    ('/wsudpproxy/?', WebSocketUDPProxyHandler),
    ('/api/?', APIHandler),
    ('/btapp/?', BtappHandler)
]

routes = { 'BITFIELD': BitmaskHandler,
           'UTORRENT_MSG': UTHandler,
           'PORT': PortHandler,
           'HAVE': HaveHandler,
           'HAVE_ALL': HaveAllHandler,
           'INTERESTED': InterestedHandler,
           'NOT_INTERESTED': NotInterestedHandler,
           'CHOKE': ChokeHandler,
           'UNCHOKE': UnChokeHandler,
           'REQUEST': RequestHandler,
           'CANCEL': CancelHandler,
           'PIECE': PieceHandler
           }

class BTApplication(object):
    def __init__(self, routes, **settings):
        self.routes = routes
        self.settings = settings
        if True or self.settings.get("debug"):
            pass
            #print 'importing autoreload'
            #import tornado.autoreload # not workin :-(
            #tornado.autoreload.start()

    def __call__(self, request):
        #logging.info('%s got request %s' % (self, request))
        if request.type in routes:
            handler_cls = routes[request.type]
            handler_cls(self, request).handle()
        else:
            logging.error('cannot handle request %s' % [request.type, request.payload])
            request.connection.stream.close()

    def log_request(self, handler):
        if options.verbose > 1:
            request_time = 1000.0 * handler.request.request_time()
            logging.info("%s %.2fms", 
                         handler._request_summary(), request_time)


class BTProtocolServer(tornado.netutil.TCPServer):
    def __init__(self, request_callback, io_loop=None):
        tornado.netutil.TCPServer.__init__(self, io_loop)
        self.request_callback = request_callback

    def handle_stream(self, stream, address):
        client.handle_connection(stream, address, self.request_callback)
        #Connection(stream, address, self.request_callback)




def let_the_streaming_begin(io_loop, bootstrap_ip_ports):
    #Setup the DHT
    dht = DHT(51414, bootstrap_ip_ports, io_loop = io_loop)
    dht.start()


    #Setup KTorrent and Its URL Handlers
    settings = dict( (k, v.value()) for k,v in options.items() )
    application = BTApplication(routes, **settings)
    Connection.ioloop = io_loop
    Connection.application = application

    settings['log_function'] = request_logger
    frontend_application = tornado.web.Application(frontend_routes, **settings)
    frontend_server = tornado.httpserver.HTTPServer(frontend_application, io_loop=io_loop)
    Connection.frontend_server = frontend_server  

    try:
        frontend_server.bind(options.frontend_port, '')
        frontend_server.start()
        #logging.info('started frontend server')
    except:
        logging.error('could not start frontend server')   


    btserver = BTProtocolServer(application, io_loop=io_loop)
    btserver.bind(options.port, '')
    btserver.start()

    logging.info('started btserver')
    logging.info('\n\n')    
  

    tornado.ioloop.PeriodicCallback( Connection.make_piece_request, 1000 * 1, io_loop=io_loop ).start()
    tornado.ioloop.PeriodicCallback( Connection.get_metainfo, 1000 * 1, io_loop=io_loop ).start() # better to make event driven
    tornado.ioloop.PeriodicCallback( Client.tick, 1000 * 1, io_loop=io_loop ).start()
    tornado.ioloop.PeriodicCallback( client.do_trackers, 1000 * 1, io_loop=io_loop ).start()
    tornado.ioloop.PeriodicCallback( client.peer_think, 3000 * 1, io_loop=io_loop ).start()
    tornado.ioloop.PeriodicCallback( Connection.cleanup_old_requests, 1000 * 1, io_loop=io_loop ).start()


    Client.resume()
    Client.http_client = httpclient.AsyncHTTPClient()
    client = Client.instances[0]

    Torrent.client = client

    def got_interrupt_signal(signum=None, frame=None):
        logging.info('got quit signal ... saving quick resume')
        Client.save_settings()
        #Torrent.save_quick_resume()
        sys.exit()

    signal.signal(signal.SIGINT, got_interrupt_signal)




if __name__ == "__main__":
    io_loop = tornado.ioloop.IOLoop()
    #io_loop.install()

    tornado.options.parse_command_line()

    #Startup the dht with some bootstrap ports
    bootstrap_ip_ports = []
    if options.bootstrap != "":
        for ip_port in options.bootstrap.split(","):
            ip_port_arr = ip_port.split(':')
            bootstrap_ip_ports.append((ip_port_arr[0],ip_port_arr[1]))

    if len(bootstrap_ip_ports) == 0:
        bht.get_dht_peers_from_torrent(options.bootstrap_torrent or "bootstrap.torrent", partial(let_the_streaming_begin, io_loop))
    else:
        let_the_streaming_begin(io_loop, bootstrap_ip_ports)
    
    


