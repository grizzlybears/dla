## -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime

import sqlite3
import data_struct 
import subprocess


 # 打开DB，并酌情建表，返回 sqlite3.Connection
def get_db_conn():
    conn = sqlite3.connect( data_struct.DB_PATH)
    conn.text_factory = str

    sql = ''' CREATE TABLE IF NOT EXISTS MdHis (
       code   TEXT 
       , t_day      TEXT
       , t_week_day TEXT
       , open  NUMERIC
       , close NUMERIC
       , high  NUMERIC
       , low   NUMERIC
       , delta_r NUMERIC
       , volume  NUMERIC
       , amount  NUMERIC
       , delta_alpha NUMBER 
       , turnover_r NUMERIC
       , PRIMARY KEY( code,t_day)
       )
    '''
    conn.execute( sql) 
    
    sql = ''' CREATE TABLE IF NOT EXISTS Settings (
       var_name  TEXT 
       , t_value     TEXT
       , n_value     NUMERIC
       , PRIMARY KEY( var_name  )
       )
    '''
    conn.execute( sql)

    conn.commit()

    return conn 

# 获得DB中的， 代码=>时间范围 
def get_inventory(dbcur):
    dbcur.execute ('''select code, count(code), min(t_day), max(t_day) 
        from MdHis 
        group by code 
        order by code 
        ''')
    r = {}

    row = dbcur.fetchone()
    while row is not None:
        one_entry =  data_struct.TDayRange()
        one_entry.count = row[1]
        one_entry.start = row[2]
        one_entry.end   = row[3]
        r[row[0]] = one_entry 
    
        row = dbcur.fetchone()
    
    return r



def save_MD_to_db( dbcur, md): 
    dbcur.execute( '''insert into  MdHis(
                code , t_day
                , open , close 
                , delta_r
                , volume , turnover_r )
            values (?, ?
                 , ?, ? 
                 , ?
                 , ? ,?
                 )'''
                , ( md.code,md.t_day
                    , md.open_price, md.close_price
                    , md.delta_r 
                    , md.volume , md.turnover_r 
                  )
                )


def gen_alpha( dbcur, base_code , target_code):
    #update MdHis 
    #set  delta_alpha = delta_r - ( select delta_r from MdHis b where b.t_day = t_day  and b.delta_r is not null and b.code =  '沪深300000300')
    #where 
    #  code ='银行'
    
    dbcur.execute( ''' update MdHis 
        set  delta_alpha = delta_r - ( select delta_r from MdHis b where b.t_day = t_day  and b.delta_r is not null and b.code = ? )
        where 
          code = ?
        '''
        , ( base_code , target_code )
        )

    r = dbcur.rowcount 

    dbcur.connection.commit()

    return r


def save_setting_basecode( dbcur, base_code ):
    dbcur.execute(
            ''' delete from Settings where var_name = ?
            '''
            , ('base_code', )
            )

    dbcur.execute(
            ''' insert into Settings (var_name, t_value) values ( ? , ?)
            '''
            , ('base_code', base_code)
            )

    dbcur.connection.commit()

