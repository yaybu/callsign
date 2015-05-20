#! /usr/bin/env python

import os
import sys
import optparse

from twisted.scripts import twistd
from twisted.python.util import sibpath

from minidns.config import config


def spawn(opts, conf):
    """ Acts like twistd """
    if opts.config is not None:
        os.environ["MINIDNS_CONFIG_FILE"] = opts.config
    sys.argv[1:] = [
        "-noy", sibpath(__file__, "minidns.tac"),
        "--pidfile", conf['pidfile'],
        "--logfile", conf['logfile'],
    ]
    twistd.run()


def run():
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", default="/etc/minidns.conf", help="path to configuration file")
    opts, args = parser.parse_args()
    conf = config(opts.config)
    spawn(opts, conf)
