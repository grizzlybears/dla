## -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime

import sqlite3
import data_struct 
import subprocess

DB_NAME='rel_research.db'

 # 打开DB，并酌情建表，返回 sqlite3.Connection
def get_db_conn():
    conn = sqlite3.connect( DB_NAME)
    conn.text_factory = str

    sql = ''' CREATE TABLE IF NOT EXISTS MdHis (
       code   TEXT 
       , t_day      TEXT
       , t_week_day TEXT
       , open  NUMERIC
       , close NUMERIC
       , high  NUMERIC
       , low   NUMERIC
       , delta   NUMERIC
       , delta_r NUMERIC
       , volume_wan  NUMERIC
       , amount_yi   NUMERIC
       , PRIMARY KEY( code,t_day)
       )
    '''
    conn.execute( sql)
    conn.commit()

    return conn 

# 获得DB中的， 代码=>时间范围 
def get_inventory(dbcur):
    dbcur.execute ("select code, count(code), min(t_day), max(t_day) from MdHis order by code ")
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
                , volume_wan)
            values (?, ?
                 , ?, ? 
                 , ?
                 , ?
                 )'''
                , ( md.code,md.t_day
                    , md.open_price, md.close_price
                    , md.delta_r 
                    , md.volume 
                  )
                )


