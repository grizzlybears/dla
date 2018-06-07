# -*- coding: utf-8 -*-
import io
import os
import sqlite3
import math
import csv

import db_operator 
import data_struct
import plotter

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

     
def correlation( dbcur, sec1, sec2):

    dbcur.execute ('''select a.t_day, a.close, a.delta_r, b.close, b.delta_r 
        from MdHis a , MdHis b
        where 
            a.code = ? and b.code = ?
            and a.t_day = b.t_day
            and a.delta_r is not null and b.delta_r is not null
        order by a.t_day 
        '''
        , (sec1.code ,sec2.code)
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

    fieldnames = ['T_Day', str(sec1), str(sec2)]
    logged_his.append( fieldnames );

    diff_his = []
    diff_his.append( ['T_Day', "%s - %s" % (str(sec1), str(sec2)) ]  )


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
    #generate_his_htm_chart( sec1, sec2, logged_his[:100])
    plotter.generate_his_htm_chart( sec1, sec2, logged_his)
    plotter.generate_diff_htm_chart( sec1, sec2, diff_his)

    return ( r_close, r_delta, row_num )

# 2D 数组 :
#  日期, ln差价, leg1涨幅, leg2涨幅
def plain_delta_for_faster_horse( logged_his,MA_Size1 = 1,  MA_Size2 = 20):

    indices = []

    for i, row in enumerate( logged_his  ):

        the_diff =  (row[1] -row[2])
        delta1 = row[5]
        delta2 = row[6]

        indices.append( 
                [
                    row[0]
                    , the_diff
                    , delta1 
                    , delta2
                ] )

    return indices 


# 2D 数组 :
#  日期, ln差价, MA1 of ln 差价,  MA2 of  ln差价 
def generate_indices_for_faster_horse( logged_his,MA_Size1 = 1,  MA_Size2 = 20):

    if 0 == MA_Size1:
        return plain_delta_for_faster_horse(logged_his)

    indices = []
    MA_Sum1 = 0
    MA_Sum2 = 0

    for index, row in enumerate( logged_his  ):

        the_diff =  (row[1] -row[2])

        if index < MA_Size1 : 
            #累加的窗口
            MA_Sum1 = MA_Sum1 + the_diff

            #部分MA
            MA1 = MA_Sum1 / (index + 1)
        else:
            # 以后的MA，窗口向后滑动一格
            MA_Sum1 = MA_Sum1 - indices[index - MA_Size1][1] +  the_diff
            
            #计算MA
            MA1 = MA_Sum1 / MA_Size1
 
        if index < MA_Size2 : 
            #累加的窗口
            MA_Sum2 = MA_Sum2 + the_diff

            #部分MA
            MA2 = MA_Sum2 / (index + 1)
        else:
            # 以后的MA，窗口向后滑动一格
            MA_Sum2 = MA_Sum2 - indices[index - MA_Size2][1] +  the_diff
            
            #计算MA
            MA2 = MA_Sum2 / MA_Size2
           
        indices.append( 
                [
                    row[0]
                    , the_diff
                    , MA1
                    , MA2
                ] )

    return indices 


# 万三手续费
TRANS_COST = math.log( 0.9997)  # −0.000300045


# 模拟换马策略
# Input:  2-D array 'logged_his'
#         日期   脚1对数化收盘价     脚2对数化收盘价     脚1收盘价  脚2收盘价
#         ...
#
# Output: 2-D array 
#         日期   脚1对数化收盘价     脚2对数化收盘价   策略对数化收盘价  换仓提示  换仓详细  
#         ...
#
def sim_faster_horse( sec1, sec2, logged_his, MA_Size1 = 1 , MA_Size2 = 20, start_day = "", end_day = ""):
    #我在excel里根据50和500的昨收，算出ln(50昨收)-ln(500昨收)，称为ln差价，ln差价求20日移动平均。
    #如果ln差价小于20日平均，持有500，反之，持有50。
    #持有50的话，当日收益为ln(50收盘)-ln(50昨收)，否则，为500的收益（当然，换股日的话，收益要减去0.0002。因为假设有万分之二的etf交易手续费）。
    #然后，将50、500、持仓的每日收益分别累积，就画出了你看到的三根线。


    # 2D 数组 :
    #  日期, ln差价, MA1 of ln 差价,  MA2 of  ln差价 
    indices = generate_indices_for_faster_horse( logged_his, MA_Size1, MA_Size2 , )   

    result = []
    trans_num = 0 
    
    ##header = [
    ##    '日期'
    ##    , "%s-%s.ln" % (str(sec1.code), str(sec2.code) )
    ##    , "MA%d" % MA_Size1 
    ##    , "MA%d" % MA_Size2 
    ##    ]

    ##plotter.simple_generate_line_chart( 
    ##         header 
    ##        , indices
    ##        )
    ##
    ##return (result ,  trans_num )


    we_hold = 0 # 0 表示'空仓'， 1 表示'脚1'， 2 表示'脚2'


    for i, row in enumerate(indices):

        if "" != start_day and row[0] < start_day:
            # 略过
            continue

        if "" != end_day and row[0] >= end_day:
            break

        #print  "\t%s\n"  %  str(row).decode('string_escape')
        
        md_that_day = logged_his[i]  #当日行情

        if i < MA_Size2 : 
            # MA(昨收差价)  还没有成型，不做操作 ，也没有损益
            result.append(
                [ row[0], md_that_day[1], md_that_day[2], 0, None, None  ]
            )
        else:
            y_diff    = indices[i - 1][1]  # 昨日ln差价
            y_diff_ma_short   = indices[i - 1][2]  # 昨日ln差价的短期MA 
            y_diff_ma_middle  = indices[i - 1][3]  # 昨日ln差价的中期MA 
            
            # 昨日本策略的收盘价
            if len(result) > 0:
                y_policy  = result[ len(result) - 1 ][3]    
            else:
                y_policy = 0

            if y_diff_ma_short < y_diff_ma_middle:
                # 脚1弱，我们应该持有脚2
                sec2_delta = md_that_day[2] - logged_his[i-1][2] #当日脚2的增量
                
                if 2 == we_hold:
                    #不用动
                    result.append(
                        [ row[0], md_that_day[1], md_that_day[2] 
                            ,  y_policy + sec2_delta 
                            , None, None  ]
                    )
                elif 1 == we_hold:
                    # 我们要从脚1换仓到脚2
                    result.append(
                        [  
                            row[0], md_that_day[1], md_that_day[2] 
                            ,  y_policy + sec2_delta + TRANS_COST + TRANS_COST 
                            , "2" , "%s %s -> %s" % ( row[0], sec1, sec2)
                        ]
                    )
                    trans_num = trans_num + 1
                    we_hold = 2
                else:
                    # 建仓脚2
                    result.append(
                        [  
                            row[0], md_that_day[1], md_that_day[2] 
                            ,  y_policy + sec2_delta + TRANS_COST 
                            , "2" , "%s 0 -> %s" %  (row[0] , sec2)
                        ]
                    )
                    trans_num = trans_num + 1
                    we_hold = 2

            elif y_diff_ma_short > y_diff_ma_middle:
                # 脚1强，我们应该持有脚1
                sec1_delta = md_that_day[1] - logged_his[i-1][1] #当日脚1的增量
                
                if 1 == we_hold:
                    #不用动
                    result.append(
                        [ row[0], md_that_day[1], md_that_day[2] 
                            ,  y_policy + sec1_delta 
                            , None, None  ]
                    )
                elif 2 == we_hold:
                    # 我们要从脚2换仓到脚1
                    result.append(
                        [  
                            row[0], md_that_day[1], md_that_day[2] 
                            ,  y_policy + sec1_delta + TRANS_COST + TRANS_COST 
                            , "1" , " %s %s -> %s" % (row[0], sec2, sec1)
                        ]
                    )
                    trans_num = trans_num + 1
                    we_hold = 1
                else:
                    # 建仓脚1
                    result.append(
                        [  
                            row[0], md_that_day[1], md_that_day[2] 
                            ,  y_policy + sec1_delta + TRANS_COST 
                            , "1" , " %s 0 -> %s" %  (row[0],sec1)
                        ]
                    )
                    trans_num = trans_num + 1
                    we_hold = 1
            else:
                # 不动
                if 1 == we_hold:
                    delta = md_that_day[1] - logged_his[i-1][1] #当日脚1的增量
                elif 2 == we_hold:
                    delta = md_that_day[2] - logged_his[i-1][2] #当日脚2的增量
                else:
                    delta = 0 
                
                result.append(
                    [ row[0], md_that_day[1], md_that_day[2] 
                        ,  y_policy + delta 
                        , None, None  ]
                )

    return (result ,  trans_num )


def bt_faster_horse( dbcur, sec1, sec2 , MA_Size1,MA_Size2 , start_day , end_day ):

    dbcur.execute ('''select a.t_day, a.close, a.delta_r, b.close, b.delta_r 
        from MdHis a , MdHis b
        where 
            a.code = ? and b.code = ?
            and a.t_day = b.t_day
            and a.delta_r is not null and b.delta_r is not null
        order by a.t_day 
        '''
        , (sec1.code ,sec2.code)
        )
   

    v_c1 = []
    v_c2 = []

    logged_his= []

    #fieldnames = ['T_Day', str(sec1), str(sec2) , '' , '' ]
    #logged_his.append( fieldnames );

    row_num = 0

    first_c1 = 0
    first_c2 = 0

    row = dbcur.fetchone()
    while row is not None:

        row_num = row_num + 1

        close1 = float(row[1] )
        close2 = float(row[3] )

        delta1 = float(row[2])
        delta2 = float(row[4])


        if 1 == row_num:
            # (相对于期初)对数化
            logged_his.append( [row[0], 0, 0,  close1, close2, delta1, delta2 ] )
            first_c1 = math.log(close1)
            first_c2 = math.log(close2)

        else:
            # (相对于期初)对数化
            logged1 = math.log(close1) - first_c1  
            logged2 = math.log(close2) - first_c2 
            logged_his.append( [
                row[0]
                , logged1 
                , logged2
                , close1
                , close2
                , delta1 
                , delta2 
                 ] )

        row = dbcur.fetchone()


    bt,trans_num  = sim_faster_horse(
            sec1,sec2, logged_his
            , MA_Size1,  MA_Size2
            , start_day , end_day)
    #return (0, row_num , trans_num, 0, 0 )
 
    suffix = ""
    if "" != start_day: 
        suffix = ".%s_%s" % (start_day, end_day)

    plotter.generate_htm_chart_for_faster_horse( sec1, sec2, bt , suffix)
    
    first_entry = bt[0]
    last_entry = bt[len(bt) - 1 ]
    net_value  =  math.exp( last_entry [3] ) 
    leg1  =  math.exp( last_entry [1] - first_entry[1] )   
    leg2  =  math.exp( last_entry [2] - first_entry[2] )   
    #net_value  =  0

    return (net_value , len(bt) , trans_num, leg1, leg2 )

  
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
            r_close,r_delta , row_num = correlation(dbcur, v1  , v2)

            one_entry = data_struct.Correlation( k1, k2, r_close, r_delta, row_num, v1.name, v2.name) 
            correls.append( one_entry) 

            db_operator.save_correl_to_db( dbcur , one_entry)
            print one_entry

            count = count +1
            #if count >= 5:
            #    break

        #if count >= 200:
        #    break



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


# 返回2D数组
# (空)    参数1   参数2    参数3   参数4 ...
# 时段1   结果    结果     结果    结果  ...
# 时段2   结果    结果     结果    结果  ...
# 时段3   结果    结果     结果    结果  ...
# ...
def faster_horse_set(dbcur, sec1 , sec2):
    paras = [
            (0,1)
            ,(1,2)
            ,(1,22)
            ,(3,22)
            ]

    scopes = [
            ""
            , "2008-01-01"
            , "2013-01-01"
            ]

    for start_day in scopes:
        for short, middle in paras:
            
            net_value, day_num, t_num, leg1 ,leg2 = bt_faster_horse(
                 dbcur, sec1, sec2, short, middle, start_day, ""
                 )
            
            print "%s %s, %s ~ , %d-%d, T=%d, V=%f, P=%f" % (
                    sec1,sec2
                    , start_day
                    , short, middle  
                    , t_num , net_value , net_value - (leg1 + leg2) / 2 
                    )



    return []


def faster_horse_all(inventory_ranges, dbcur):

    fha = {}

    count = 0
    for k1,v1  in inventory_ranges.iteritems():
        
        s = {}

        for k2,v2  in inventory_ranges.iteritems():
            if k1 >= k2:
                continue;
            
            # print "%s %s" % (k1,k2)
            r = faster_horse_set(dbcur, v1 , v2)
            
            s[k2] =  r

            count = count +1
            #if count >= 5:
            #    break
        
        fha[k1] = s
        #if count >= 200:
        #    break


def fetch_md_his_for_faster_horse2( dbcur, secs):
    select_clause = ""
    from_clause   = ""
    where_filter  = ""
    join_clause   = ""
    more_filter   = ""

    for i,sec in enumerate(secs):
        if 0 == i:
            select_clause = "select " + "t0.t_day" 
            from_clause   = "from MdHis t0"
            where_filter  = "where \n\tt0.code = '%s' " % sec.code
        else:
            from_clause   = from_clause  + ", MdHis t%d" % i
            where_filter  = where_filter + " and t%d.code = '%s' " % (i, sec.code)
            join_clause   = join_clause + " and t0.t_day = t%d.t_day" % i

        select_clause = select_clause + ", t%d.close, t%d.delta_r" % (i,i)
        more_filter   = more_filter + " and t%d.delta_r is not null" % i

    sql = "%s\n%s\n%s\n%s\n%s\n" % (select_clause, from_clause, where_filter, join_clause ,more_filter )

    print sql
    return []


def faster_horse2( dbcur, secs, MA_Size1,MA_Size2 , start_day , end_day ):
    
    md_his_data = fetch_md_his_for_faster_horse2( dbcur, secs)

    return 
   
    v_c1 = []
    v_c2 = []

    logged_his= []

    #fieldnames = ['T_Day', str(sec1), str(sec2) , '' , '' ]
    #logged_his.append( fieldnames );

    row_num = 0

    first_c1 = 0
    first_c2 = 0

    row = dbcur.fetchone()
    while row is not None:

        row_num = row_num + 1

        close1 = float(row[1] )
        close2 = float(row[3] )

        delta1 = float(row[2])
        delta2 = float(row[4])


        if 1 == row_num:
            # (相对于期初)对数化
            logged_his.append( [row[0], 0, 0,  close1, close2, delta1, delta2 ] )
            first_c1 = math.log(close1)
            first_c2 = math.log(close2)

        else:
            # (相对于期初)对数化
            logged1 = math.log(close1) - first_c1  
            logged2 = math.log(close2) - first_c2 
            logged_his.append( [
                row[0]
                , logged1 
                , logged2
                , close1
                , close2
                , delta1 
                , delta2 
                 ] )

        row = dbcur.fetchone()


    bt,trans_num  = sim_faster_horse(
            sec1,sec2, logged_his
            , MA_Size1,  MA_Size2
            , start_day , end_day)
    #return (0, row_num , trans_num, 0, 0 )
 
    suffix = ""
    if "" != start_day: 
        suffix = ".%s_%s" % (start_day, end_day)

    plotter.generate_htm_chart_for_faster_horse( sec1, sec2, bt , suffix)
    
    first_entry = bt[0]
    last_entry = bt[len(bt) - 1 ]
    net_value  =  math.exp( last_entry [3] ) 
    leg1  =  math.exp( last_entry [1] - first_entry[1] )   
    leg2  =  math.exp( last_entry [2] - first_entry[2] )   
    #net_value  =  0

    return (net_value , len(bt) , trans_num, leg1, leg2 )


