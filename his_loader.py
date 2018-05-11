# -*- coding: utf-8 -*-
import csv
import io
import pdb

import sqlite3
import db_operator 
import data_struct

def check_col_name( filename,row, col_name):
    if col_name not in row:
        raise Exception("%s, csv文件格式有异，没有列'%s'" % (filename,col_name)  )


def verify_csv_format( filename, row ):

    col_num = len(row)

    if 11 != col_num:
        raise Exception("%s, csv文件格式有异，不是11列" % filename  )

    check_col_name( filename, row, '时间')
    check_col_name( filename, row, '开盘')
    check_col_name( filename, row, '收盘')
    check_col_name( filename, row, '最高')
    check_col_name( filename, row, '最低')
    check_col_name( filename, row, '涨幅%')
    check_col_name( filename, row, '总手(万)')
    check_col_name( filename, row, '金额(亿)')
    
    return

def load_some(filename ,dbcur, inventory_ranges ):
    the_file = io.open( filename, "r", encoding='utf-8')
    reader = csv.DictReader( the_file, dialect = 'excel-tab')
    #reader = csv.reader( the_file, dialect = 'excel-tab')

    row_num = 0
    the_code = ""
            
    # 取 src 中 '.' 之前的部分作为 code
    # Bank.txt.utf8 ==> 'Bank'
    the_code = filename.split('.')[0]

    for row in reader:
        row_num +=1

        if 1== row_num:
            verify_csv_format(filename, row ) 
            
        #s = str(row).decode('string_escape').decode('utf8')  #  能显示 DectReader吐的中文
        #s = row[0].decode('utf8')    #<= OK，能显示 plain reader 吐的
        #.decode('string_escape')
        #print s
        #pdb.set_trace()

        md_record =  data_struct.MdRecord()
        md_record.code = the_code 
        md_record.load_from_csvrow( row)
        md_record.dump()

        db_operator.save_MD_to_db( dbcur, md_record)


