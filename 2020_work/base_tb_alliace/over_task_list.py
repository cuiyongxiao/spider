# coding=utf-8
"""任务列表页，第一步"""
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
from httprequest_beta import query_request,query_request_bytes
import traceback
import re
from config import config
from dbpool import db_al,db_proxy
from magiclogger import initlog_file
from emailsend import MailSend
from util import time_calculator
from apscheduler.schedulers.background import BackgroundScheduler



db=db_proxy
# db=Dbpool()

driver=None

TASK_LIST_URL='https://pub.alimama.com/cpa/event/list.json'
TODAY=time.strftime('%Y.%m.%d',time.localtime(time.time()))
cookie = ""
logger=logging.getLogger("log")





def insert_into_db(item_list):
    succ=False
    try:
        for item in item_list:
            status=item.get('status')
            event_name=item.get('event_name')
            seller_nick=item.get('seller_nick')
            status_desc=item.get('status_desc')
            event_id=item.get('event_id')
            seller_id=item.get('seller_id')
            shop_keeper_id=item.get('shop_keeper_id')
            seller_wangwang=item.get('seller_wangwang')
            start_time=item.get('start_time')
            end_time=item.get('end_time')


            sql = "select status from spider.alliance_task_list where event_id={};".format(event_id)
            db_stat = db.execute_data(sql)
            succ = db_stat.get("succ")
            datas = db_stat.get("data")
            '''
            -1 失效
            1-4  正常
            5 已结算
            '''
            if datas:
                if datas[0][0]==5:
                    sql = 'update spider.alliance_task_list set shop_status=1 where event_id={};'.format(event_id)
                    db_state = db.execute_data(sql)
                    print('{} 已完结'.format(event_id))
                    continue
                if datas[0][0]!=5:
                    if status<0:
                        # sql = 'delete from spider.alliance_task_list where event_id={};'.format(event_id)
                        # db_state = db.execute_data(sql)
                        sql = 'update spider.alliance_task_list set shop_status=1 where event_id={};'.format(event_id)
                        db_state = db.execute_data(sql)
                        print('{} 已失效'.format(event_id))

                    elif status>0:
                        # sql = 'REPLACE INTO spider.alliance_task_list(status,event_name,seller_nick,status_desc,event_id,seller_id,shop_keeper_id,seller_wangwang,start_time,end_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
                        sql = 'update spider.alliance_task_list set status={},status_desc="{}",start_time="{}",end_time="{}",shop_status="{}" where event_id={};'.format(status,status_desc,start_time,end_time,'0',event_id)
                        db_state = db.execute_data(sql)
                        succ = db_state.get("succ")
                        if succ:
                            print('event_id {} update succ'.format(event_id))
            # if not datas and status>0:
            if not datas :
                if status>0:
                    """数据为新，插入"""

                    sql = 'INSERT INTO spider.alliance_task_list(status,event_name,seller_nick,status_desc,event_id,seller_id,shop_keeper_id,' \
                          'seller_wangwang,start_time,end_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
                    data = (status, str(event_name), str(seller_nick), str(status_desc), event_id, seller_id, shop_keeper_id,
                    str(seller_wangwang), str(start_time), str(end_time))
                    db_state = db.execute_data(sql, data)
                    succ = db_state.get("succ")
                    if succ:
                        print('event_id {} insert succ'.format(event_id))
                if status<0:
                    sql = 'INSERT INTO spider.alliance_task_list(status,event_name,seller_nick,status_desc,event_id,seller_id,shop_keeper_id,' \
                          'seller_wangwang,start_time,end_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
                    data = (status, str(event_name), str(seller_nick), str(status_desc), event_id, seller_id, shop_keeper_id,
                    str(seller_wangwang), str(start_time), str(end_time))
                    db_state = db.execute_data(sql, data)
                    succ = db_state.get("succ")

                    sql = 'update spider.alliance_task_list set shop_status=1 where event_id={};'.format(event_id)
                    db_state = db.execute_data(sql)

                    if succ:
                        print('event_id {} insert succ'.format(event_id))

    except Exception as e:
        print('list error')
        # logger.exception(str(e))
    return succ




def sql_select_port():
    """从数据库中查询数据"""
    succ=False
    datas=""
    try:
        sql = "select ip,port from ruhnn_crawler.spider_proxy where status =1 order by created_at desc limit 0,10;"
        db_stat = db.execute_data(sql)
        succ = db_stat.get("succ")
        datas = db_stat.get("data")
        return succ,datas
    except Exception as e:
        logger.exception(str(e))
    return succ,datas

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




def requests_taobao(cookie,page):
    succ = False
    info = None
    try:
        q_params=dict()
        url=TASK_LIST_URL
        headers = {"authority":"pub.alimama.com",
"method":"GET",
"scheme":"https",
"accept":"application/json, text/javascript, */*; q=0.01",
"accept-encoding":"gzip, deflate, br",
"accept-language":"zh,en-NZ;q=0.9,en;q=0.8,zh-CN;q=0.7",
"query_data-type":"application/x-www-form-urlencoded",
"cookie":cookie,
"referer":"https://pub.alimama.com/manage/task/index.htm?spm=a219t.7900221.1998910419.10.4ea875a5NnuMbq",
"user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
"x-requested-with":"XMLHttpRequest"
        }
        params = {"status":"",
"q":"",
"toPage":"{}".format(page),
"perPageSize":"1000",
"t":"1587004152053",
"_tb_token_":"736e887888b83",
"coopType":"1",
"pvid":""}

        #q_params['proxies']=proxies
        q_params['headers']=headers
        q_params['params'] = params

        succ,info = query_request(url,**q_params)
    except Exception as e:
        logger.info(str(e))
    return succ,info



def analyzer_info(info):
    """解析任务列表页信息"""
    result = dict()
    item_list=list()
    shop_name=None
    goods_num=None
    try:
        j_info = json.loads(info)
        if j_info.get('ok')!=True:
            logger.info('maybe info get fail {}'.format(info))
            return
        data_list=j_info.get('data').get('result')
        for data in data_list:
            status=data.get('status')
            # if status<0:
            #     continue
            data_dict=dict()
            data_dict['status']=status
            data_dict['event_name']=data.get('eventName')
            data_dict['seller_nick']=data.get('sellerNick')
            data_dict['status_desc']=data.get('statusDesc')
            data_dict['event_id']=data.get('eventId')
            data_dict['seller_id']=data.get('sellerId')
            data_dict['shop_keeper_id']=data.get('shopKeeperId')
            data_dict['seller_wangwang']=data.get('sellerWangwang')
            data_dict['start_time']=data.get('startTime')
            data_dict['end_time']=data.get('endTime')
            item_list.append(data_dict)
        # total_page=data.get('totalPages')
    except Exception as e:
        logger.info(str(e))
    return item_list




def action(cookie):
    try:
        succ_proxy, proxy_list = sql_select_port()
        if not succ_proxy:
            logger.info("proxy get fail")
            return
        proxies = get_proxy(proxy_list)
        for page in range(1,4):
            succ,info = requests_taobao(cookie,page)
            if succ and info:
                item_list = analyzer_info(info)
                if not item_list:
                    print('邮件报警')
                    message='淘宝联盟任务列表数据为空'
                if item_list:

                    succ = insert_into_db(item_list)
                    if not succ:
                        logger.info('update task_list fail date{}'.format(TODAY))
                    print('task_list {} succ'.format(page))
    except Exception as e:
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



def main():
    succ,cookie=get_cookie()
    action(cookie)

if __name__ == '__main__':
    log_file=config.get("log_dir_taobao")+"task_list"
    initlog_file(filename=log_file,file_allow=True)
    main()
