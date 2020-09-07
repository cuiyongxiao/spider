# coding=utf-8
"""每天更新任务详情页第一页，第二步（2）"""
import logging
import time
from lxml import etree
from urllib.parse import quote
import subprocess
import selenium
import requests
from urllib import parse
from emailsend import MailSend
import hashlib
import json
import random
from httprequest_beta import query_request, query_request_bytes
import traceback
import re
from config import config
from dbpool import db_al, db_proxy
from magiclogger import initlog_file
from emailsend import MailSend
from util import time_calculator
from apscheduler.schedulers.background import BackgroundScheduler

db = db_proxy
# db=Dbpool()
logger = logging.getLogger("log")

driver = None

MANAGE_URL = 'https://pub.alimama.com/common/adzone/adzoneManage.json'
TODAY = time.strftime('%Y.%m.%d', time.localtime(time.time()))
cookie = ""



def send_email(subject, to_email, message):
    succ_send = False
    try:
        succ_send = MailSend().send_email_simple_ssl(subject, to_email, message)
    except Exception as e:
        logger.exception(str(e))
    return succ_send


def send_email_warning(message):
    subject = "淘宝联盟-邮件"
    fail_email_accpeter = ['cuiyx@ruhnn.com']
    succ_send = send_email(subject, to_email=fail_email_accpeter, message=message)
    logger.info("send_succ" + str(succ_send))






def update_presum_status(event_id):
    succ = False
    try:
        sql = "update spider.alliance_detail set presum_status =0 where event_id ={};".format(event_id)
        db_state = db.execute_data(sql)
        succ = db_state.get("succ")
    except Exception as e:
        logger.exception(str(e))
    return succ


def insert_into_db(item_list):

    succ = False
    try:
        for result in item_list:
            mix_alipay_num_30day = result['mix_alipay_num_30day']
            mix_alipay_rec_30day = result['mix_alipay_rec_30day']
            site_id = result['site_id']
            member_id = result['member_id']
            pid = result['pid']
            adzone_id = result['adzone_id']
            site_name = result['site_name']
            mix_click_30day = result['mix_click_30day']
            rec_30day = result['rec_30day']
            name = result['name']
            sql = 'replace into spider.alliance_adzone_manage (pid,pid_name,site_name,mix_alipay_num_30day,mix_alipay_rec_30day,mix_click_30day,rec_30day,member_id,adzone_id,site_id) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
            data =(str(pid),name,site_name,mix_alipay_num_30day,mix_alipay_rec_30day,mix_click_30day,rec_30day,member_id,adzone_id,site_id)
            db_state = db.execute_data(sql, data)
            succ = db_state.get("succ")
            if succ:
                print('replace succ')
    except Exception as e:
        logger.exception(str(e))
    return succ






def sql_select_port():
    """从数据库中查询数据"""
    succ = False
    datas = ""
    try:
        sql = "select ip,port from ruhnn_crawler.spider_proxy where status =1 order by created_at desc limit 0,10;"
        db_stat = db.execute_data(sql)
        succ = db_stat.get("succ")
        datas = db_stat.get("data")
        return succ, datas
    except Exception as e:
        logger.exception(str(e))
    return succ, datas


def get_proxy(proxy_list):
    try:
        proxy = random.sample(proxy_list, 1)
        ip = proxy[0][0]
        port = proxy[0][1]
        proxies = {'https': "https://" + str(ip) + ":" + str(port)}
        logger.info('proxy: ' + str(proxies))
        return proxies
    except Exception as e:
        logger.exception(str(e))


def get_proxy_ip_port(proxy_list):
    try:
        proxy = random.sample(proxy_list, 1)
        ip = proxy[0][0]
        port = proxy[0][1]
        proxies = {'https': "https://" + str(ip) + ":" + str(port)}
        logger.info('proxy: ' + str(proxies))
        return ip, port
    except Exception as e:
        logger.exception(str(e))


def requests_taobao(cookie, proxies):
    succ = False
    info = None
    try:
        q_params = dict()
        url = MANAGE_URL
        headers = {"authority": "pub.alimama.com",
                   "method": "GET",
                   "path": "/cpa/event/list.json?status=&q=&toPage=1&perPageSize=40&t=1550215085070&_tb_token_=736e887888b83&pvid=",
                   "scheme": "https",
                   "accept": "application/json, text/javascript, */*; q=0.01",
                   "accept-encoding": "gzip, deflate, br",
                   "accept-language": "zh,en-NZ;q=0.9,en;q=0.8,zh-CN;q=0.7",
                   "query_data-type": "application/x-www-form-urlencoded",
                   "cookie": cookie,
                   "referer": "https://pub.alimama.com/manage/task/index.htm?spm=a219t.7900221.1998910419.10.4ea875a5NnuMbq",
                   "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
                   "x-requested-with": "XMLHttpRequest"
                   }
        params = {"spm":"a219t.7900221.1998910419.11.3aaf75a56qWmyQ",
"tab":"3",
"toPage":"1",
"perPageSize":"4000",
"gcid":"8",
"t":"1587006093587",
"pvid":"60_115.238.95.52_980_1587006087247",
"_tb_token_":"7d78dee87eee",
"_input_charset":"utf-8"}
        # q_params['proxies'] = proxies
        q_params['headers'] = headers
        q_params['params'] = params
        q_params["timeout"] = (7, 7)

        # succ, info = query_request(url, **q_params)

        info = requests.get(url=url, **q_params).text
        succ = True


    except Exception as e:
        logger.info(str(e))
    return succ, info




def analyzer_info(info):
    """解析任务列表页信息"""
    item_list = list()
    shop_name = None
    goods_num = None
    try:
        j_info = json.loads(info)
        if j_info.get('ok') != True:
            logger.info('maybe info get fail {}'.format(info))
            return
        page_list = j_info.get('data').get('pagelist')
        for item in page_list:
            result= dict()
            result['mix_alipay_num_30day'] = item.get('mixAlipayNum30day')
            result['mix_alipay_rec_30day'] = item.get('mixAlipayRec30day')
            result['site_id'] = item.get('siteid')
            result['member_id'] = item.get('memberid')
            result['pid'] = item.get('adzonePid')
            result['adzone_id'] = item.get('adzoneid')
            result['site_name'] = item.get('sitename')
            result['mix_click_30day'] = item.get('mixClick30day')
            result['rec_30day'] = item.get('rec30day')
            result['name'] = item.get('name')
            item_list.append(result)
        # total_page=data.get('totalPages')
    except Exception as e:
        logger.info(str(e))
    return item_list








def action(cookie):
    try:
        succ_proxy, proxy_list = sql_select_port()


        while True:
            proxies = get_proxy(proxy_list)
            print('start manage')
            succ, info = requests_taobao(cookie, proxies)
            if succ and info:
                result = analyzer_info(info)
                if not result:
                    print('邮件报警')
                    message = '淘宝联盟推广位数据为空'
                    send_email_warning(message)
                if result:

                    succ = insert_into_db(result)
                    if succ:
                        print('adzone_manage succ')
                        break
                    if not succ:
                        logger.info('fail adzone_manage date{}'.format(TODAY))
    except Exception as e:
        print('manage 失败')
        logger.error(str(e))


def get_cookie():
    """从数据库中查询数据"""
    succ=False
    data=""
    try:
        sql = "select cookie from spider.alliance_cookie where id=1;"
        db_stat = db.execute_data(sql)
        succ = db_stat.get("succ")
        datas = db_stat.get("data")
        if datas:
            data=datas[0][0]
    except Exception as e:
        logger.exception(str(e))
    return succ,data


def select_item_id():
    succ = False
    datas = list()
    try:
        sql = "select d.event_id,l.shop_keeper_id from spider.alliance_detail d join spider.alliance_task_list l on d.event_id=l.event_id where d.presum_status=1;"
        db_stat = db.execute_data(sql)
        succ = db_stat.get("succ")
        if not succ:
            return False
        datas = db_stat.get("data")
    except Exception as e:
        logger.exception(str(e))
    logger.info("now db has shops len:" + str(len(datas)))
    return succ, datas


def old_get_cookie():
    with open('./cookie.txt', 'r') as f:
        cookie = f.read()
        f.close()
    return cookie

def main():
    try:
        succ,cookie = get_cookie()
        action(cookie)
    except Exception as e:
        logger.error(str(e))


if __name__ == '__main__':
    main()

