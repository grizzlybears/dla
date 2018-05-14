# -*- coding: utf-8 -*-
import io
import os
import sqlite3
import db_operator 
import data_struct

def print_inventory(inventory_ranges):
    for k,v  in inventory_ranges.iteritems():
        print "%s\t %s ~ %s, %d records. " % (k.ljust(20), v.start, v.end , v.count) 


# memo of 'correl' 
# 
# https://www.investopedia.com/ask/answers/031015/how-can-you-calculate-correlation-using-excel.asp
# 
# http://www.statisticshowto.com/probability-and-statistics/correlation-coefficient-formula/
#
# https://stackoverflow.com/questions/3949226/calculating-pearson-correlation-and-significance-in-python#
