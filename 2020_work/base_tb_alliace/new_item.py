# coding=utf-8
"""每天更新任务详情页第一页，第二步（1）"""
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

# EVENT_DETAIL_URL = 'https://pub.alimama.com/cpa/event/detail.json'
EVENT_DETAIL_URL = 'https://pub.alimama.com/cpa/event/itemInfoList.json'
TODAY = time.strftime('%Y.%m.%d', time.localtime(time.time()))
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


# print(len(item_list))
# input(item_list)

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

#代理
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


def get_new():
    # sql = "select event_id,shop_keeper_id,status from spider.alliance_task_list where shop_status=0 and status!=4;"
    sql = "select event_id from spider.alliance_goods where item_id is null"
    db_stat = db.execute_data(sql)
    datas = db_stat.get("data")  # event_id

    succ, cookie = get_cookie()

    item_list = []
    for i in datas:
        event_id = i[0]
        print(event_id)
        sql = "select shop_keeper_id from spider.alliance_task_list where event_id={}".format(event_id)
        db_stat = db.execute_data(sql)
        try:
            shop_keeper_id = db_stat.get("data")[0][0]  #
        except:
            continue
        data = [event_id, shop_keeper_id]
        item_list.append(data)


    good_list=[]

    for _ in range(10):
        for item in item_list:
            it_len=len(datas)
            if item[0] in good_list:
                continue

            succ_proxy, proxy_list = sql_select_port()
            proxies = get_proxy(proxy_list)

            # action(item[0], item[1], cookie, item[2])
            q_params = dict()
            url = EVENT_DETAIL_URL
            #time.sleep(0.3)
            headers = {"authority": "pub.alimama.com",
                       "method": "GET",
                       # "path": "/cpa/event/list.json?status=&q=&toPage=1&perPageSize=40&t=1550215085070&_tb_token_=736e887888b83&pvid=",
                       "scheme": "https",
                       "accept": "application/json, text/javascript, */*; q=0.01",
                       "accept-encoding": "gzip, deflate, br",
                       "accept-language": "zh,en-NZ;q=0.9,en;q=0.8,zh-CN;q=0.7",
                       "query_data-type": "application/x-www-form-urlencoded",
                       "cookie": cookie,
                       "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
                       # "x-requested-with": "XMLHttpRequest"
                       }
            params = {"eventId": item[0],
                      "shopKeeperId": item[1],
                      "onlyBasicInfo": "false",
                      "t": "1550223899211",
                      "_tb_token_": "736e887888b83",
                      "pvid": ""}
            # "itemName":"张大奕辛普森工装羽绒服女短款2018新款白鹅绒时尚情侣加厚羽绒衣"}
            q_params['proxies'] = proxies
            q_params['headers'] = headers
            q_params['params'] = params

            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "accept-encoding": "gzip, deflate,br",
                "accept-language": "zh-CN,zh;q=0.8",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36",
                "upgrade-insecure-requests": "1"
            }

            q_params = q_params if q_params else {}
            q_header = q_params.get("headers")

            headers.update(q_header) if q_header else headers

            q_params["headers"] = headers
            q_params["timeout"] = (2, 7)
            try:
                rep = requests.get(url=url, **q_params).text
                # input(rep)
            except:
                print("重试请求")
                # time.sleep(1)
                continue


            try:
                result = dict()

                j_info = json.loads(rep)
                if j_info.get('ok') != True:
                    logger.info('maybe info get fail {}'.format(rep))
                    time.sleep(1)
                    print('提取重试')
                    continue
                event_item = j_info.get('data').get('result')[0]
                result['itemId'] = event_item.get('itemId')

            except:
                print('提取错误')
                time.sleep(1)
                continue
            print(result)

            itemId=result['itemId']
            sql = 'update spider.alliance_goods set item_id=%s where event_id=%s;'
            data = (itemId, item[0])

            db_state = db.execute_data(sql, data)
            succ = db_state.get("succ")
            if succ:
                print('event_id {} detail succ'.format(item[0]))
            else:
                print('写入失败')

            good_list.append(item[0])
            g_len = len(good_list)
            need_ = it_len - g_len
            print("还有{}需要更新".format(str(need_)))

    print('new item end ')
    return 'succ'
def main():
    print('start new item')
    get_new()

if __name__ == '__main__':
    main()
