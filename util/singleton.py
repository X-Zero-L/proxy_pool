# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     singleton
   Description :
   Author :        JHao
   date：          2016/12/3
-------------------------------------------------
   Change Activity:
                   2016/12/3:
-------------------------------------------------
"""
__author__ = 'JHao'


class Singleton(type):
    """
    Singleton Metaclass
    """

    _inst = {}

    def __call__(self, *args, **kwargs):
        if self not in self._inst:
            self._inst[self] = super(Singleton, self).__call__(*args)
        return self._inst[self]
