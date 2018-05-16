# -*- coding: utf-8 -*-

import sqlite3

WORKING_DIR = "working_dir"
JSLIB       = "jslib"
HTML_TEMPL  = "html_template"
TEMPL_A     = "%s/template_A.html" % HTML_TEMPL 
TEMPL_B     = "%s/template_B.html" % HTML_TEMPL 
DB_PATH     = "%s/dla.db" % WORKING_DIR
HTML_INDEX  = "%s/_index.html" %WORKING_DIR 


# 日线记录
class MdRecord:
 
    #代码
    code = ""

    #交易日 YYYY-MM-DD
    t_day = ""

    #开盘价 float 
    open_price = None
 
    #收盘价 float 
    close_price = None

    #最高价 float 
    high_price = None

    #最低
    low_price= None

    #涨跌幅% float
    delta_r= None

    #换手率
    turnover_r =None

    #手数
    volume = 0

    #成交金额 float
    ammount = 0.0

 
    def dump(self, indent = "  "):
         print "%s %s @%s 开=%s 收=%s 涨幅=%s%% "  % ( indent
                , self.code
                , self.t_day
                , str(self.open_price)
                , str(self.close_price)
                , str(self.delta_r) 
                )
 
    def dump_all(self, indent = "  "):
         print "%s %s @%s 开=%s 收=%s 涨幅=%s%%  总手=%s" % ( indent
                , self.code
                , self.t_day
                , str(self.open_price)
                , str(self.close_price)
                , str(self.delta_r) 
                , str(self.volume)
                )


    def patch_code(self, src):
        # 取 src 中 '.' 之前的部分作为 code
        # Bank.txt.utf8 ==> 'Bank'
        self.code = src.split('.')[0]

    def load_from_csvrow( self, row):

        # '时间': '2018-05-07,一'
        self.t_day = row['时间'].split(',')[0]

        # '开盘': '6209.73'
        t = row['开盘']
        if '--' == t :
            self.open_price = None
        else:
            self.open_price = float(t)

        # '收盘': '1004.71' 
        t = row['收盘']
        if '--' == t :
            self.close_price = None
        else:
            self.close_price = float(t)

        # '涨幅%': '1.23'  其实是 1.23% 的意思 
        if row.has_key('涨幅%'): 
            t = row['涨幅%']
        else:
            t = row['涨幅'].split('%')[0]
        
        if '--' == t :
            self.delta_r = None
        else:
            self.delta_r = float(t)

        # '总手(万)': '499848920'
        if row.has_key('总手(万)'): 
            t = row['总手(万)']
        else:
            t = row['总手'].replace(',', '')

        if '--' == t :
            self.volume = None
        else:
            self.volume = float(t)


# 时间范围 YYYY-MM-DD
class TDayRange:
    start = ""
    end   = ""
    count = 0


