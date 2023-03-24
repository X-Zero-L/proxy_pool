# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     check
   Description :   执行代理校验
   Author :        JHao
   date：          2019/8/6
-------------------------------------------------
   Change Activity:
                   2019/08/06: 执行代理校验
                   2021/05/25: 分别校验http和https
                   2022/08/16: 获取代理Region信息
-------------------------------------------------
"""
__author__ = 'JHao'

from util.six import Empty
from threading import Thread
from datetime import datetime
from util.webRequest import WebRequest
from handler.logHandler import LogHandler
from helper.validator import ProxyValidator
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler


class DoValidator(object):
    """ 执行校验 """

    conf = ConfigHandler()

    @classmethod
    def validator(cls, proxy, work_type):
        """
        校验入口
        Args:
            proxy: Proxy Object
            work_type: raw/use
        Returns:
            Proxy Object
        """
        http_r = cls.httpValidator(proxy)
        https_r = cls.httpsValidator(proxy) if http_r else False

        proxy.check_count += 1
        proxy.last_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        proxy.last_status = bool(http_r)
        if http_r:
            if proxy.fail_count > 0:
                proxy.fail_count -= 1
            proxy.https = bool(https_r)
            if work_type == "raw":
                proxy.region = cls.regionGetter(proxy) if cls.conf.proxyRegion else ""
        else:
            proxy.fail_count += 1
        return proxy

    @classmethod
    def httpValidator(cls, proxy):
        return all(func(proxy.proxy) for func in ProxyValidator.http_validator)

    @classmethod
    def httpsValidator(cls, proxy):
        return all(func(proxy.proxy) for func in ProxyValidator.https_validator)

    @classmethod
    def preValidator(cls, proxy):
        return all(func(proxy) for func in ProxyValidator.pre_validator)

    @classmethod
    def regionGetter(cls, proxy):
        try:
            url = f"https://searchplugin.csdn.net/api/v1/ip/get?ip={proxy.proxy.split(':')[0]}"
            r = WebRequest().get(url=url, retry_time=1, timeout=2).json
            return r['data']['address']
        except:
            return 'error'


class _ThreadChecker(Thread):
    """ 多线程检测 """

    def __init__(self, work_type, target_queue, thread_name):
        Thread.__init__(self, name=thread_name)
        self.work_type = work_type
        self.log = LogHandler("checker")
        self.proxy_handler = ProxyHandler()
        self.target_queue = target_queue
        self.conf = ConfigHandler()

    def run(self):
        self.log.info(f"{self.work_type.title()}ProxyCheck - {self.name}: start")
        while True:
            try:
                proxy = self.target_queue.get(block=False)
            except Empty:
                self.log.info(f"{self.work_type.title()}ProxyCheck - {self.name}: complete")
                break
            proxy = DoValidator.validator(proxy, self.work_type)
            if self.work_type == "raw":
                self.__ifRaw(proxy)
            else:
                self.__ifUse(proxy)
            self.target_queue.task_done()

    def __ifRaw(self, proxy):
        if proxy.last_status:
            if self.proxy_handler.exists(proxy):
                self.log.info(f'RawProxyCheck - {self.name}: {proxy.proxy.ljust(23)} exist')
            else:
                self.log.info(f'RawProxyCheck - {self.name}: {proxy.proxy.ljust(23)} pass')
                self.proxy_handler.put(proxy)
        else:
            self.log.info(f'RawProxyCheck - {self.name}: {proxy.proxy.ljust(23)} fail')

    def __ifUse(self, proxy):
        if proxy.last_status:
            self.log.info(f'UseProxyCheck - {self.name}: {proxy.proxy.ljust(23)} pass')
            self.proxy_handler.put(proxy)
        elif proxy.fail_count > self.conf.maxFailCount:
            self.log.info(
                f'UseProxyCheck - {self.name}: {proxy.proxy.ljust(23)} fail, count {proxy.fail_count} delete'
            )
            self.proxy_handler.delete(proxy)
        else:
            self.log.info(
                f'UseProxyCheck - {self.name}: {proxy.proxy.ljust(23)} fail, count {proxy.fail_count} keep'
            )
            self.proxy_handler.put(proxy)


def Checker(tp, queue):
    """
    run Proxy ThreadChecker
    :param tp: raw/use
    :param queue: Proxy Queue
    :return:
    """
    thread_list = [
        _ThreadChecker(tp, queue, f"thread_{str(index).zfill(2)}")
        for index in range(20)
    ]
    for thread in thread_list:
        thread.setDaemon(True)
        thread.start()

    for thread in thread_list:
        thread.join()
