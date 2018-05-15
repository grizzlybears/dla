# -*- coding: utf-8 -*-
import io
import os
import sqlite3
import db_operator 
import data_struct

from scipy.stats.stats import pearsonr

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

def correlation( dbcur,code1, code2):

    dbcur.execute ('''select a.t_day, a.close, a.delta_r, b.close, b.delta_r 
        from MdHis a , MdHis b
        where 
            a.code = ? and b.code = ?
            and a.t_day = b.t_day
            and a.delta_r is not null and b.delta_r is not null
        order by a.t_day 
        '''
        , (code1 ,code2)
        )


    v_delta_r1 = []
    v_delta_r2 = []
    v_c1 = []
    v_c2 = []

    row = dbcur.fetchone()
    while row is not None:

        #print ("%s -- %s %f %f , %s %f %f " % (row[0], code1, row[1] , row[2], code2, row[3], row[4])  )
        v_delta_r1.append ( float(row[2]) * 1000 )    # 数据库里是百分数，我们希望变量正规化 [-1,1] 分布
        v_delta_r2.append ( float(row[4]) * 1000 )

        v_c1.append ( float(row[1] ))
        v_c2.append ( float(row[3] ))

    
        row = dbcur.fetchone()
    

    r_delta,p    = pearsonr(v_delta_r1 ,v_delta_r2 )
    r_close,p2  = pearsonr(v_c1 ,v_c2 )
    print "%s %s , 收盘价关联度 = %f，涨跌幅关联度 = %f" % ( code1, code2, r_close, r_delta )



