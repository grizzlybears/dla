# -*- coding: utf-8 -*-
import csv
import io
import os
import re
import pdb

import sqlite3
import db_operator 
import data_struct

def check_col_name( filename,row, col_name):
    if col_name not in row:
        s = str(row).decode('string_escape').decode('utf8')  #  能显示 DectReader吐的中文
        print s
        raise Exception("%s, csv文件格式有异，没有列'%s'" % (filename,col_name)  )

def check_col_name2( filename,row, col1,col2):
    if col1 not in row  and col2 not in row: 
        s = str(row).decode('string_escape').decode('utf8')  #  能显示 DectReader吐的中文
        print s
        raise Exception("%s, csv文件格式有异，没有列'%s'" % (filename,col1)  )



def verify_his_csv_format( filename, row ):

    col_num = len(row)

    if  col_num < 11:
        raise Exception("%s, 历史行情csv文件格式有异，不满11列" % filename  )

    check_col_name( filename, row, '时间')
    check_col_name( filename, row, '开盘')
    check_col_name( filename, row, '收盘')
    check_col_name( filename, row, '最高')
    check_col_name( filename, row, '最低')
    check_col_name2( filename, row,'涨幅', '涨幅%')
    check_col_name2( filename, row,'总手', '总手(万)')
    check_col_name2( filename, row, '金额', '金额(亿)')

    #check_col_name( filename, row, '总手(万)')
    #check_col_name( filename, row, '金额(亿)')
    
    return

def verify_daily_csv_format( filename, row ):

    col_num = len(row)

    if  col_num < 14:
        raise Exception("%s, 每日行情汇总csv文件格式有异，不满14列" % filename  )

    check_col_name( filename, row, '代码')
    check_col_name( filename, row, '开盘')
    check_col_name( filename, row, '现价')#就是 '收盘'
    check_col_name( filename, row, '最高')
    check_col_name( filename, row, '最低')
    check_col_name2( filename, row,'涨幅', '涨幅%')
    check_col_name2( filename, row,'总手', '总手(万)')
    check_col_name2( filename, row, '金额', '金额(亿)')

    #check_col_name( filename, row, '总手(万)')
    #check_col_name( filename, row, '金额(亿)')
    
    check_col_name2( filename, row, '名称', '名称    ')
    return


def load_some(filepath,dbcur, inventory_ranges ):
    basename = os.path.basename( filepath )
    no_ext  = basename.split('.')[0]
    ma =  re.match( '^\d{8}$' , no_ext )

    if ma:
        # 如果是八位数字文件名(不含扩展名)，则认为是每日行情汇总文件 
        load_daily_md(filepath, no_ext, dbcur, inventory_ranges )
    else:
        # 否则一律当作历史行情文件处理
        load_md_his(filepath,dbcur, inventory_ranges )


    # 读入每日行情汇总文件
    #代码	名称    	.	现价	涨幅%	5日涨幅	10日涨幅	20日涨幅	年初至今	涨跌	金额	现手	总手	开盘	最高	最低	振幅%	量比	
    #SH000001	上证指数	--	3193.30	1.24	+0.95%	+3.31%	+3.30%	-3.44%	+39.02	168038060000	878000	13651692000	3151.08	3193.45	3144.78	1.54	1.09	
    #SH000002	Ａ股指数	--	3344.54	1.24	+0.95%	+3.31%	+3.31%	-3.43%	+40.94	167879790000	874000	13628998000	3300.24	3344.70	3293.61	1.55	1.09	
    #SH000003	Ｂ股指数	--	319.91	0.45	-0.47%	+1.07%	-0.14%	-6.41%	+1.42	158267980	4000	22694300	318.52	320.23	318.21	0.634	1.12	
    #SH000004	工业指数	--	2618.51	1.54	+1.88%	+4.68%	+4.63%	-0.78%	+39.72	113509645000	657100	8721595800	2577.09	2618.67	2574.33	1.72	1.12	
    #....
def load_daily_md(filepath, yyyymmdd, dbcur, inventory_ranges ):
    with  io.open( filepath, "r", encoding='utf-8') as the_file:
        reader = csv.DictReader( the_file, dialect = 'excel-tab')

        row_num = 0
        
        for row in reader:
            row_num +=1

            if 1== row_num:
                verify_daily_csv_format(filepath, row ) 
        
            md_record = data_struct.MdRecord()
            r = md_record.load_from_daily_csv_row( filepath, row, yyyymmdd)

            if  not r:
                continue
            
            # 如果某证券从未由‘历史’文件倒入过，那么不会在SecurityInfo里有记录，所以
            # 不能  if  md_record.code  not in  inventory_ranges: xxxx
            #

            info = data_struct.SecurityInfo( )
            info.code = md_record.code 
            info.name = md_record.name 
            #info.dump()
            db_operator.save_sec_info_to_db_if_not_exists(dbcur, info)

            db_operator.save_MD_to_db( dbcur, md_record)
    
    print "%s was imported" % filepath

    # 读入行情历史文件
    # 格式:
    #     电力881145.txt.utf8
    #时间	开盘	最高	最低	收盘	涨幅	振幅	总手	金额	换手%	成交次数	
    #2007-08-01,三	1010.109	1010.109	943.346	943.346	--	--	1,092,894,600	13,566,472,000	0	0	
    #2007-08-02,四	944.755	972.780	944.755	972.780	+3.12%	2.97%	687,798,450	8,794,664,200	0	0	
    #2007-08-03,五	979.302	981.402	979.302	981.402	+0.89%	0.22%	872,775,680	10,147,507,400	0	0	
    #2007-08-06,一	990.741	1010.642	990.741	1010.642	+2.98%	2.03%	1,091,771,050	12,634,076,300	0	0	
    #2007-08-07,二	1014.942	1014.942	997.878	997.878	-1.26%	1.69%	1,002,823,210	12,288,118,100	0	0	
    #2007-08-08,三	994.111	994.111	981.575	981.575	-1.63%	1.26%	770,776,370	10,059,957,200	0	0	
    #...
def load_md_his(filepath ,dbcur, inventory_ranges ):
    the_file = io.open( filepath, "r", encoding='utf-8')
    reader = csv.DictReader( the_file, dialect = 'excel-tab')
    #reader = csv.reader( the_file, dialect = 'excel-tab')

    row_num = 0
            
    info = data_struct.SecurityInfo( ) 
    info.parse_from_filepath( filepath )
    the_code = info.code
    #info.dump()
    db_operator.save_sec_info_to_db(dbcur, info)

    if the_code in  inventory_ranges:
        the_range = inventory_ranges[the_code]
    else:
        the_range = None
    #print the_range

    for row in reader:
        row_num +=1

        if 1== row_num:
            verify_his_csv_format(filepath, row ) 
            
        #s = str(row).decode('string_escape').decode('utf8')  #  能显示 DectReader吐的中文
        #s = row[0].decode('utf8')    #<= OK，能显示 plain reader 吐的
        #.decode('string_escape')
        #print s
        #pdb.set_trace()

        md_record =  data_struct.MdRecord()
        md_record.code = the_code 
        md_record.load_from_his_csv_row( row)
        #md_record.dump()

        if the_range is not None \
            and md_record.t_day >= the_range.start \
            and md_record.t_day <= the_range.end :
                continue

        db_operator.save_MD_to_db( dbcur, md_record)

    print "%s was imported" % filepath
    the_file.close()

def codes_from_file( filepath):
    with io.open( filepath, "r", encoding='utf-8') as f:
        content = f.read().splitlines()

    #print content 

    return content 

