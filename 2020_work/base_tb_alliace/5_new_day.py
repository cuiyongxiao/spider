# -*- coding=utf8 -*-
# coding=utf-8
"""手动输入淘宝联盟cookie"""
import logging
import time
import os
import adzone_manage
import event_detail
import event_effect
import event_effect2
import event_goods
import event_presum
import event_coopinfo
# import read_csv
import new_adzone
import new_read_csv  # 多线程
import task_list
import over_task_list
import report
import datetime
import subprocess
from urllib import parse
import hashlib
import json
import succ_send
import random
from httprequest_beta import query_request, query_request_bytes
import traceback
import re
from config import config
from magiclogger import initlog_file
from open_chrome import AlimamaLogin
from apscheduler.schedulers.background import BackgroundScheduler
import day_tread
from dbpool import db_al, db_proxy
import new_item
db = db_proxy
ALLIANCE_URL = "https://pub.alimama.com/"
LIVE_URL = "https://taobaolive.taobao.com/room/index.htm?spm=a21tn.8216370.2278280.2.23285722QCkt7h&feedId=2fd05fb9-00a7-4df2-8190-1b1c50ed2eb7"

# db=Dbpool()
logger = logging.getLogger("log")


def update_cookie(cookie):
    succ = False
    try:
        sql = 'update spider.alliance_cookie set cookie ="{}" where id=1;'.format(cookie)
        db_state = db.execute_data(sql)
        succ = db_state.get("succ")
        if succ:
            print('succ cookie')
    except Exception as e:
        logger.exception(str(e))
    return succ


def sycm_login():
    cookie = None
    try:
        #
        cookie = input('输入cookie')
        cookie = re.sub('%', '%%', cookie)
        update_cookie(cookie)
        print('成功更新cookie，开始跑程序')
        # task_list.main()
        over_task_list.main()
        print('coopinfo begin')
        event_coopinfo.main()
        print('detail begin')
        event_detail.main()
        # 整合多线程获取数据
        day_tread.main()
        # adzone_manage.main()
        new_adzone.main()
        # read_csv.main()
        new_read_csv.main()
        report.main()
        succ_send.send_email()
        new_item.main()


    except Exception as e:
        print(str(e))
    return cookie


def main():
    # new_item.main()
    # input('end')
    sycm_login()


if __name__ == '__main__':
    log_file = config.get("log_dir_taobao") + "get_cookie"
    initlog_file(filename=log_file, file_allow=True)
    main()
    # 定时操作，每小时运行一次
    """
    sched = BackgroundScheduler()

    sched.add_job(main, 'cron', hour='9',minute='30',second='0',coalesce=True)
    # sched.add_job(action, 'interval',seconds=10,id="cron_task")
    try:
        sched.start()
    except Exception as e:
        print(str(e))

    while True:
        time.sleep(10)
    """
