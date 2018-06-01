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
    
def array_content_to_file(the_file, var_name, the_array): 
    the_file.write( "var %s = \n" % var_name  );
    the_file.write( str( the_array).decode('string_escape'))
    the_file.write( "\n;\n"   );



def generate_js_data_w_head( jsfilename,  logged_his):
    with io.open( jsfilename, "wb" ) as js_file:
        array_content_to_file( js_file, "header" , logged_his[0:1])
        array_content_to_file( js_file, "raw_data" , logged_his[1:])

def generate_js_head_n_data( jsfilename, header, data ):
    with io.open( jsfilename, "wb" ) as js_file:
        array_content_to_file( js_file, "header" , [header])
        array_content_to_file( js_file, "raw_data" , data)

def write_chart_html_header( the_file, jsfilename, sec1, sec2):
    the_file.write(" <html>\n<head>\n<title>%s %s</title>\n" % ( str(sec1) ,str(sec2) ))

    the_file.write(" <script type=\"text/javascript\" src=\"ggchart_loader.js\"></script>\n")
    the_file.write(" <script type=\"text/javascript\" src=\"%s\"></script>\n" %  jsfilename )

    the_file.write( 
    '''
    <script type="text/javascript">
      google.charts.load('current', {'packages':['corechart']});
      google.charts.setOnLoadCallback(drawChart);

      function drawChart() {
      ''');
    

def draw_chart_full( the_file, sec1, sec2, additional_options = ""):

    s = '''
        var options = {
          title: '$title$',
          curveType: 'function',
          legend: { position: 'bottom' }
          , height:550
          %s
        };

        var chart1 = new google.visualization.LineChart(document.getElementById('curve_chart1'));
        var data1 = google.visualization.arrayToDataTable(
                header.concat( raw_data)
                );
        chart1.draw(data1, options);


        ''' % additional_options 

    the_file.write( 
            s.replace( 
                '$title$' , "%s %s, history" % ( str(sec1) ,str(sec2) ) 
                )
            )
def chart_div_full(the_file):    
    the_file.write(" <div id=\"curve_chart1\" ></div>\n")


def draw_chart_last_x( the_file, sec1, sec2, x , subvar , additional_options = "" ): 

    the_file.write( 
            '''var options_%d = { 
                title: '%s %s, last %d', 
                curveType: 'function', 
                legend: { position: 'bottom' } , height:550
                %s  
                };\n
                '''
                % (subvar, str(sec1) ,str(sec2), x , additional_options )
                )

    the_file.write("    var chart_%d = new google.visualization.LineChart(document.getElementById('curve_chart_%d'));\n" 
            %  (subvar, subvar)
            )
 
    the_file.write("    var data_%d = google.visualization.arrayToDataTable( header.concat( raw_data.slice( - %d  ) ));\n" 
            % (subvar, x ) 
            )

    the_file.write("    chart_%d.draw(data_%d, options_%d);\n\n" % (subvar, subvar,  subvar) 
            )

def chart_div_subvar(the_file, subvar):    
    the_file.write(" <div id=\"curve_chart_%d\"></div>\n" % subvar)

def head_end_body_begin( the_file):
    the_file.write("}\n </script>\n </head>\n <body>\n")


def html_end( the_file):
    the_file.write(" </body>\n</html>\n")


def generate_htm_chart_3lines_w_annotation( sec1, sec2, bt ):
    return 


def generate_2lines_chart( line1_name, line2_name, data):
    jsfilename = "%s_%s.js" % ( line1_name, line2_name)
    jsfilepath = "%s/%s" % (data_struct.WORKING_DIR, jsfilename) 
    generate_js_head_n_data (jsfilepath,  ['日期', line1_name, line2_name ] , data)
 
    filename = "%s/%s_%s.html" % (data_struct.WORKING_DIR, line1_name, line2_name)
    with io.open( filename, "wb" ) as the_file:
        write_chart_html_header( the_file, jsfilename, line1_name, line2_name ) 
        draw_chart_full( the_file, line1_name, line2_name  )

        if len(data) > 1000:
            draw_chart_last_x( the_file, line1_name, line2_name , 600 , 1 )
            draw_chart_last_x( the_file, line1_name, line2_name , 300 , 2 )

        head_end_body_begin( the_file)
        chart_div_full(the_file)
        
        if len(data) > 1000:
        
            chart_div_subvar( the_file,1 )
            chart_div_subvar( the_file,2 )

        html_end( the_file)



def generate_his_htm_chart( sec1, sec2, logged_his):
    
    jsfilename = "%s_%s.js" % ( sec1.code, sec2.code)
    jsfilepath = "%s/%s" % (data_struct.WORKING_DIR, jsfilename) 
    generate_js_data_w_head(jsfilepath,  logged_his )
 
    filename = "%s/%s_%s.html" % (data_struct.WORKING_DIR, sec1.code, sec2.code)
    with io.open( filename, "wb" ) as the_file:
        write_chart_html_header( the_file, jsfilename,  sec1, sec2) 
        draw_chart_full( the_file, sec1, sec2,  )

        if len(logged_his) > 1000:
            draw_chart_last_x( the_file, sec1, sec2, 600 , 1 )
            draw_chart_last_x( the_file, sec1, sec2, 300 , 2 )

        head_end_body_begin( the_file)
        chart_div_full(the_file)
        
        if len(logged_his) > 1000:
        
            chart_div_subvar( the_file,1 )
            chart_div_subvar( the_file,2 )

        html_end( the_file)



def generate_diff_htm_chart( sec1, sec2, diff_his): 
    
    jsfilename = "%s_%s.diff.js" % ( sec1.code, sec2.code)
    jsfilepath = "%s/%s" % (data_struct.WORKING_DIR, jsfilename) 
    generate_js_data_w_head(jsfilepath,   diff_his )
    
    filename = "%s/%s_%s.diff.html" % (data_struct.WORKING_DIR, sec1.code, sec2.code)

    additional_options =  ',colors: [\'black\']' 
    with io.open( filename, "wb" ) as the_file:
        write_chart_html_header( the_file, jsfilename, sec1, sec2) 
        draw_chart_full( the_file, sec1, sec2, additional_options  )

        if len(diff_his) > 1000:
            draw_chart_last_x( the_file, sec1, sec2, 600 , 1 , additional_options  )
            draw_chart_last_x( the_file, sec1, sec2, 300 , 2 , additional_options  )

        head_end_body_begin( the_file)
        chart_div_full(the_file)
        
        if len(diff_his) > 1000:
        
            chart_div_subvar( the_file,1 )
            chart_div_subvar( the_file,2 )

        html_end( the_file)


     
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
    generate_his_htm_chart( sec1, sec2, logged_his)
    generate_diff_htm_chart( sec1, sec2, diff_his)

    return ( r_close, r_delta, row_num )


# 模拟换马策略
# Input:  2-D array 'logged_his'
#         日期   脚1对数化收盘价     脚2对数化收盘价     脚1收盘价  脚2收盘价
#         ...
#
# Output: 2-D array 
#         日期   脚1对数化收盘价     脚2对数化收盘价   策略对数化收盘价  换仓提示  换仓详细  
#         ...
#
def sim_faster_horse( sec1, sec2, logged_his, MA_Size = 20):
    #我在excel里根据50和500的昨收，算出ln(50昨收)-ln(500昨收)，称为ln差价，ln差价求20日移动平均。
    #如果ln差价小于20日平均，持有500，反之，持有50。
    #持有50的话，当日收益为ln(50收盘)-ln(50昨收)，否则，为500的收益（当然，换股日的话，收益要减去0.0002。因为假设有万分之二的etf交易手续费）。
    #然后，将50、500、持仓的每日收益分别累积，就画出了你看到的三根线。

    # 2D 数组 :
    #  日期, ln差价,  MA(20) of  ln差价
    indices = []
    MA_Sum = 0
    for index, row in enumerate( logged_his  ):

        the_diff =  (row[1] -row[2])

        if index <= (MA_Size - 1): 
            
            #累加的窗口
            MA_Sum = MA_Sum + the_diff


            #部分MA
            MA = MA_Sum / (index + 1)

            indices.append( 
                [
                    row[0]
                    , the_diff 
                    , MA
                ] )
        else:
            # 以后的MA，窗口向后滑动一格
            MA_Sum = MA_Sum - indices[index - MA_Size][1] +  the_diff
            
            #计算MA
            MA = MA_Sum / MA_Size
            
            indices.append( 
                [
                    row[0]
                    , the_diff
                    , MA
                ] )

    generate_2lines_chart( "ln%s-%s" % (str(sec1.code), str(sec2.code) )
            , "MA%d" % MA_Size 
            , indices[0:200] )


def bt_faster_horse( dbcur, sec1, sec2):

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

        if 1 == row_num:
            # (相对于期初)对数化
            logged_his.append( [row[0], 0, 0,  close1, close2 ] )
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
                 ] )

        row = dbcur.fetchone()


    #generate_his_csv( code1, code2, logged_his)
    #generate_his_htm_chart( sec1, sec2, logged_his[:100])
    bt = sim_faster_horse(sec1,sec2, logged_his, 5)
    bt = sim_faster_horse(sec1,sec2, logged_his, 10)
    bt = sim_faster_horse(sec1,sec2, logged_his, 20)

    generate_htm_chart_3lines_w_annotation( sec1, sec2, bt )
    
    #net_value  =  math.exp( bt[len(bt)][3] ) 
    net_value  =  0

    return (net_value , row_num )

  
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

