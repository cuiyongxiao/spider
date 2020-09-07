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

EVENT_DETAIL_URL = 'https://pub.alimama.com/cpa/event/detail.json'
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

succ, cookie = get_cookie()

sql = "select event_id,shop_keeper_id,status from spider.alliance_task_list where shop_status=0 and status!=4;"
db_stat = db.execute_data(sql)
succ = db_stat.get("succ")

datas = db_stat.get("data") #  event_id , shop_keeper , status

#datas=[(7328, 125878120, 3),(7324, 14213650, 3), (7325, 486080184, 3),(7305, 349940029, 3), (7306, 349940029, 3), (7307, 31357592, 3), (7308, 126522961, 3), (7309, 126522961, 3), (7310, 324480078, 3), (7317, 121157278, 3)]
# datas=[(11008, 815520009, 3)]
def send_email(subject, to_email, message):
    succ_send = False
    succ_send = MailSend().send_email_simple_ssl(subject, to_email, message)
    return succ_send


def send_email_warning(message):
    subject = "淘宝联盟-邮件"
    fail_email_accpeter = ['cuiyx@ruhnn.com']

    succ_send = send_email(subject, to_email=fail_email_accpeter, message=message)


def main():
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


    good_list=[]

    for _ in range(10):
        for item in datas:
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
            params = {"eventId": item[0],
                      "shopKeeperId": item[1],
                      "onlyBasicInfo": "false",
                      "t": "1585191260371",
                      "_tb_token_": "7d78dee87eee",
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
            except:
                print("重试请求")
                # time.sleep(1)
                continue

            s = re.findall('nologin', rep)

            if len(s) != 0:

                send_email_warning('login error')
                input('登陆异常')


            try:
                result = dict()

                j_info = json.loads(rep)
                if j_info.get('ok') != True:
                    logger.info('maybe info get fail {}'.format(rep))
                    time.sleep(1)
                    print(rep)
                    print('提取重试')
                    continue
                event_item = j_info.get('data').get('eventItem')
                event_rule = j_info.get('data').get('eventRule')
                basicInfo = j_info.get('data').get('basicInfo')
                result['auction_url'] = event_item.get('auctionUrl')
                result['title'] = event_item.get('title')
                result['category_name'] = event_item.get('categoryName')
                result['category_id'] = event_item.get('categoryId')
                result['item_id'] = event_item.get('itemId')
                pic_url = event_item.get('picUrl')
                result['pic_url'] = "https:{}".format(pic_url)
                result['zk_price'] = event_item.get('zkPrice')
                result['uv_price'] = event_rule.get('uvPrice')
                result['uv_count'] = event_rule.get('uvCount')
                result['rule_type_name'] = event_rule.get('ruleTypeName')
                result['total_amount'] = event_rule.get('totalAmount')
                result['targetAlipayAmt'] = event_rule.get('targetAlipayAmt')


                # 'targetAlipayAmt'
                result['channel_name_list'] = event_rule.get('channelNameList')
                result['startTime'] = basicInfo.get('startTime')
                result['endTime'] = basicInfo.get('endTime')
                result['eventName'] = basicInfo.get('eventName')
            except:
                print('提取错误')
                time.sleep(1)
                continue
            print(result)

            uv_price = result['uv_price']
            uv_count = result['uv_count']
            total_amount = result['total_amount']
            startTime = result['startTime']
            endTime = result['endTime']
            eventName = result['eventName']
            targetAlipayAmt = result['targetAlipayAmt']
            sql = 'update spider.alliance_detail set uv_price=%s,uv_count=%s,total_amount=%s,start_time=%s,end_time=%s,event_name=%s,targetAlipayAmt=%s where event_id=%s;'
            data = (uv_price, uv_count, total_amount, startTime, endTime, eventName,targetAlipayAmt, item[0])

            db_state = db.execute_data(sql, data)
            succ = db_state.get("succ")
            if succ:
                print('event_id {} detail succ'.format(item[0]))
            else:
                input('写入失败')

            good_list.append(item[0])
            g_len = len(good_list)
            need_ = it_len - g_len
            print("还有{}需要获取".format(str(need_)))

if __name__ == '__main__':
    main()

