# -*- coding=utf8 -*-
# coding=utf-8
"""单品分析页面，直接访问网址保存excel，从excel中把文件保存进数据库中
商品效果页面获取所有的单品item_id
需要模拟登陆"""
import logging
import time
from urllib.parse import quote
import datetime
import subprocess
import selenium
import requests
from urllib import parse
from pycookiecheat import chrome_cookies
import hashlib
import json
import random
from httprequest_beta import query_request,query_request_bytes
import traceback
import re
from config import config
from dbpool import db_al,db_proxy
from magiclogger import initlog_file
from util import time_calculator
from open_chrome import AlimamaLogin
from apscheduler.schedulers.background import BackgroundScheduler

ALLIANCE_URL="https://pub.alimama.com/"


db = db_proxy
# db=Dbpool()
logger=logging.getLogger("log")

def get_cookies_from_chrome():
    cookies = None
    try:
        url=ALLIANCE_URL
        cookies = chrome_cookies(url,cookie_file='/Users/power/Library/Application Support/Google/Chrome/Default/Cookies')
        time.sleep(2)
        kvs = [item[0] + "=" + item[1] for item in cookies.items()]
        cookies = ";".join(kvs)
    except Exception as e:
        logger.exception(str(e))
    return cookies

def read_txt(cookie):
    with open('./cookie.txt','w') as f:
        f.write(cookie)
        f.close()


def update_cookie(cookie):
    succ = False
    try:
        sql = 'update spider.alliance_cookie set cookie ="{}" where id=1;'.format(cookie)
        db_state = db.execute_data(sql)
        succ = db_state.get("succ")
    except Exception as e:
        logger.exception(str(e))
    return succ


def sycm_login():
    cookie = None
    try:
        suc = AlimamaLogin(need_switch=True).action()
        if suc:
            time.sleep(10)
            cookie = get_cookies_from_chrome()
            cookie=re.sub('%','%%',cookie)
            update_cookie(cookie)
            logger.info('cookie succ')
            AlimamaLogin().close_chrome()

        # print(cookie)
        """
        global driver
        succ=init_brower()
        if succ:
            # driver.get('https://sycm.taobao.com/custom/login.htm?_target=http://sycm.taobao.com/portal/home.htm')
            driver.get('https://login.taobao.com/member/login.jhtml?from=sycm&full_redirect=true&style=minisimple&minititle=&minipara=0,0,0&sub=true&redirect_url=http://sycm.taobao.com/portal/home.htm')
            time.sleep(2)
            # driver.maximize_window()
            user= driver.find_element_by_xpath("//*[@id='TPL_username_1']");
            user.send_keys(user_name)

            # driver.switch_to_input('TPL_username_1')
            # time.sleep(2)
            # driver.find_element_by_id('TPL_password_1').send_keys(u'qunzi123456')
            pw= driver.find_element_by_xpath("//*[@id='TPL_password_1']");
            for i in password:
                time.sleep(random.random())
                pw.send_keys(i)
            time.sleep(2)
            driver.find_element_by_id('J_SubmitStatic').click()
            """
    except Exception as e:
        print(str(e))
    return cookie


def main():
    # update_cookie(1)
    sycm_login()

if __name__ == '__main__':
    log_file=config.get("log_dir_taobao")+"get_cookie"
    initlog_file(filename=log_file,file_allow=True)
    # shopinfo_action()
    main()
    # 定时操作，每小时运行一次

    sched = BackgroundScheduler()

    sched.add_job(main, 'cron', hour='10',minute='5,10,20',second='0',coalesce=True)
    # sched.add_job(action, 'interval',seconds=10,id="cron_task")
    try:
        sched.start()
    except Exception as e:
        print(str(e))

    while True:
        time.sleep(10)
