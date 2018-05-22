# -*- coding: utf-8 -*-
import io
import os
import sqlite3
import math
import csv

import db_operator 
import data_struct

from scipy.stats.stats import pearsonr

def print_inventory(inventory_ranges):
    for k,v  in inventory_ranges.iteritems():
        print "%s%s\t %s ~ %s, %d records. " % (k.ljust(10),v.name, v.start, v.end , v.count) 


# memo of 'correl' 
# 
# https://www.investopedia.com/ask/answers/031015/how-can-you-calculate-correlation-using-excel.asp
# 
# http://www.statisticshowto.com/probability-and-statistics/correlation-coefficient-formula/
#
# https://stackoverflow.com/questions/3949226/calculating-pearson-correlation-and-significance-in-python#

def generate_his_csv( code1, code2, logged_his):
    filename = "%s/%s_%s.csv" % (data_struct.WORKING_DIR, code1, code2)
    #the_file = io.open( filename, "w", encoding='utf-8')
    the_file = io.open( filename, "wb" )

    writer = csv.writer(the_file)
    #writer.writerow ( fieldnames)
    writer.writerows ( logged_his)

    the_file.close()
    
def generate_his_htm_chart( code1, code2, logged_his):
    filename = "%s/%s_%s.html" % (data_struct.WORKING_DIR, code1, code2)
    html_file = io.open( filename, "wb" )

    template_A_file = io.open( data_struct.TEMPL_A , "r") 
    template_A = str( template_A_file.read() )
    template_A_file.close()

    template_B_file = io.open( data_struct.TEMPL_B , "r") 
    template_B = str( template_B_file.read())
    template_B_file.close()

    html_file.write( template_A.replace( '$title$' , "%s %s" % (code1,code2) ) )

    html_file.write( str( logged_his).decode('string_escape'))

    html_file.write( "\n")
    html_file.write( template_B.replace('$more_chart_options$', '' ) )

    html_file.close()
 
def generate_diff_htm_chart( code1, code2, diff_his):
    filename = "%s/%s_%s.diff.html" % (data_struct.WORKING_DIR, code1, code2)
    html_file = io.open( filename, "wb" )

    template_A_file = io.open( data_struct.TEMPL_A , "r") 
    template_A = str( template_A_file.read() )
    template_A_file.close()

    template_B_file = io.open( data_struct.TEMPL_B , "r") 
    template_B = str( template_B_file.read())
    template_B_file.close()

    html_file.write( template_A.replace( '$title$' , "diff of (%s - %s)" % (code1,code2) ) )

    html_file.write( str( diff_his).decode('string_escape'))

    html_file.write( "\n")
    html_file.write( template_B.replace('$more_chart_options$', ',colors: [\'black\']' ) )

    html_file.close()
     
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
   
   #
   # 根据 涨跌幅_aplha  来计算 涨跌幅关联度， 结果等同于直接用 涨跌幅计算
   # dbcur.execute ('''select a.t_day, a.close, a.delta_alpha, b.close, b.delta_alpha 
   #     from MdHis a , MdHis b
   #     where 
   #         a.code = ? and b.code = ?
   #         and a.t_day = b.t_day
   #         and a.delta_alpha is not null and b.delta_alpha is not null
   #     order by a.t_day 
   #     '''
   #     , (code1 ,code2)
   #     )



    v_delta_r1 = []
    v_delta_r2 = []
    v_c1 = []
    v_c2 = []

    logged_his= []

    fieldnames = ['T_Day', "%s logged" % code1, "%s logged" % code2]
    logged_his.append( fieldnames );

    diff_his = []
    diff_his.append( ['T_Day', "%s - %s" % (code1, code2) ]  )


    row_num = 0

    first_c1 = 0
    first_c2 = 0

    row = dbcur.fetchone()
    while row is not None:

        row_num = row_num + 1

        #print ("%s -- %s %f %f , %s %f %f " % (row[0], code1, row[1] , row[2], code2, row[3], row[4])  )
        #v_delta_r1.append ( float(row[2]) * 1000 )    # 数据库里是百分数，我们希望变量正规化 [-1,1] 分布
        v_delta_r1.append ( float(row[2]) )
        v_delta_r2.append ( float(row[4]) )

        close1 = float(row[1] )
        close2 = float(row[3] )

        #v_c1.append ( close1 ) # 直接考察收盘价的关联度
        #v_c2.append ( close2 )

        if 1 == row_num:
            # (相对于期初)对数化
            logged_his.append( [row[0], 0 , 0  ] )
            first_c1 = math.log(close1)
            first_c2 = math.log(close2)

            v_c1.append(0)   # 考察对数化之后的收盘价的关联度
            v_c2.append(0)

            diff_his.append( [row[0], 0] );

        else:

            # (相对于期初)对数化
            logged1 = round( math.log(close1) - first_c1 , 4 )
            logged2 = round( math.log(close2) - first_c2 , 4 )
            logged_his.append( [
                row[0]
                , logged1 
                , logged2
                 ] )

            v_c1.append(logged1) # 考察对数化之后的收盘价的关联度
            v_c2.append(logged2)
            diff_his.append( [row[0], round ( logged1 - logged2 , 4 ) ] );

        row = dbcur.fetchone()
    

    r_delta,p    = pearsonr(v_delta_r1 ,v_delta_r2 )
    r_close,p2  = pearsonr(v_c1 ,v_c2 )

    #generate_his_csv( code1, code2, logged_his)
    generate_his_htm_chart( code1, code2, logged_his)
    generate_diff_htm_chart( code1, code2, diff_his)

    return ( r_close, r_delta, row_num )

   
def cmp_correl( correl1, correl2):
    k1 = correl1.r_close + correl1.r_delta 
    k2 = correl2.r_close + correl2.r_delta 

    if k1 < k2 :
        return 1

    if k1 > k2 :
        return -1

    return 0

def gen_alpha( dbcur, base_code):
    inventory_ranges = db_operator.get_inventory(dbcur)

    if base_code  not in inventory_ranges:
        print "'%s' was not in DB." % base_code
        return

    entry = inventory_ranges[base_code]
    if entry.count < 2000:
        print "'%s' 日线不足2000，不能作为‘基准’指数。" % base_code
        return 


    for k1,v1  in inventory_ranges.iteritems():
        if k1 == base_code:
            continue
        r = db_operator.gen_alpha(dbcur, base_code, k1)
        print "generated aplha in  %d records of code = '%s'" % (r, k1)

    db_operator.save_setting_basecode( dbcur, base_code)


def correlation_all(inventory_ranges, dbcur):

    correls = []

    count = 0
    for k1,v1  in inventory_ranges.iteritems():
        for k2,v2  in inventory_ranges.iteritems():
            if k1 <= k2:
                continue;
                # print "%s %s" % (k1,k2)
            r_close,r_delta , row_num = correlation(dbcur, k1  , k2)

            one_entry = data_struct.Correlation( k1, k2, r_close, r_delta, row_num, v1.name, v2.name) 
            correls.append( one_entry) 

            db_operator.save_correl_to_db( dbcur , one_entry)
            print one_entry

            count = count +1
            if count >= 5:
                break

        if count >= 200:
            break



    correls_sorted = sorted( correls, cmp = cmp_correl )
    
    print correls_sorted
    
    html_file = io.open( data_struct.HTML_INDEX , "wb" )
    html_file.write("<html><body>\n" )

    for cor  in correls_sorted:
        html_file.write("<a href=%s_%s.html> %s%s - %s%s </a>: 收盘价相关度=%f, 涨跌幅相关度=%f, 记录数 = %d\n "
                % (cor.code1, cor.code2
                    , cor.code1, cor.name1,cor.code2,cor.name2 
                    , cor.r_close , cor.r_delta , cor.record_num )
                )
        html_file.write("&nbsp;&nbsp; <a href=%s_%s.diff.html> 'chart of diff'</a><br>\n "
                % (cor.code1, cor.code2 )
                )


    html_file.write("</body></html>\n" )

    html_file.close()

