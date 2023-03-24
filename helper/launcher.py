# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     launcher
   Description :   启动器
   Author :        JHao
   date：          2021/3/26
-------------------------------------------------
   Change Activity:
                   2021/3/26: 启动器
-------------------------------------------------
"""
__author__ = 'JHao'

import sys
from db.dbClient import DbClient
from handler.logHandler import LogHandler
from handler.configHandler import ConfigHandler

log = LogHandler('launcher')


def startServer():
    __beforeStart()
    from api.proxyApi import runFlask
    runFlask()


def startScheduler():
    __beforeStart()
    from helper.scheduler import runScheduler
    runScheduler()


def __beforeStart():
    __showVersion()
    __showConfigure()
    if __checkDBConfig():
        log.info('exit!')
        sys.exit()


def __showVersion():
    from setting import VERSION
    log.info(f"ProxyPool Version: {VERSION}")


def __showConfigure():
    conf = ConfigHandler()
    log.info(f"ProxyPool configure HOST: {conf.serverHost}")
    log.info(f"ProxyPool configure PORT: {conf.serverPort}")
    log.info(f"ProxyPool configure PROXY_FETCHER: {conf.fetchers}")


def __checkDBConfig():
    conf = ConfigHandler()
    db = DbClient(conf.dbConn)
    log.info("============ DATABASE CONFIGURE ================")
    log.info(f"DB_TYPE: {db.db_type}")
    log.info(f"DB_HOST: {db.db_host}")
    log.info(f"DB_PORT: {db.db_port}")
    log.info(f"DB_NAME: {db.db_name}")
    log.info(f"DB_USER: {db.db_user}")
    log.info("=================================================")
    return db.test()
