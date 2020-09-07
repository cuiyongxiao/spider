# coding=utf-8
""""""
import logging
import time
import datetime
import pandas as pd
from dbpool import db_al, db_proxy
from queue import Queue
import threading
import random

db = db_proxy
logger = logging.getLogger("log")

TODAY = time.strftime('%Y.%m.%d', time.localtime(time.time()))


def select_item_id():
    succ = False
    datas = list()
    try:
        sql = "select event_id from spider.alliance_task_list where effect_status=1;"
        db_stat = db.execute_data(sql)
        succ = db_stat.get("succ")
        if not succ:
            return False
        datas = db_stat.get("data")
    except Exception as e:
        logger.exception(str(e))
    logger.info("now db has shops len:" + str(len(datas)))
    return succ, datas


def read_csv(file_name):
    item_list = list()
    try:
        df = pd.DataFrame(pd.read_excel(io=file_name,keep_default_na=False))
        #df1 = df[['时间', '商家昵称', '活动id', 'pid', '渠道名称', 'uv数', '加购人数', '收藏人数', '付款笔数', '付款金额']]
        df1 = df[['时间', '商家昵称', '活动id', 'pid', '渠道名称', '付款金额', '进店uv数', '付款笔数', '收藏人数', '加购人数']]

        # df1.fillna(value=0)
        df1.where(df1.notnull(), None)
        info_list = df1.get_values()

        for info in info_list:
            array_list = info.tolist()
            array_dict = dict()
            array_dict['时间'] = array_list[0]
            array_dict['商家昵称'] = array_list[1]
            array_dict['活动id'] = array_list[2]
            array_dict['pid'] = array_list[3]
            array_dict['渠道名称'] = array_list[4]
            array_dict['进店uv数'] = array_list[6]
            array_dict['加购人数'] = array_list[9]
            array_dict['收藏人数'] = array_list[8]
            array_dict['付款笔数'] = array_list[7]
            array_dict['付款金额'] = array_list[5]
            if array_list[9]!=array_list[9]:
                array_dict['付款金额'] = float(0)
            if array_dict['渠道名称']=='':
                continue
            item_list.append(array_dict)



    except Exception as e:
        print(str(e))
    return item_list


def insert_into_db(item_list):
    succ = False
    try:

        for item in item_list:
            sql_select = "select count(1) from spider.alliance_effect where date_time='{}' and event_id={} and pid='{}' and channel='{}'".format(
                item.get('时间'), item.get('活动id'), item.get('pid'),item.get('渠道名称'))
            db_state = db.execute_data(sql_select)
            succ = db_state.get('succ')
            count = db_state.get('data')[0][0]
            if count == 1:
                "表存在"
                # print('{},{} db has exist'.format(item_id, date_time))
                continue
            if item.get('渠道名称')=='':
                continue
            sql = 'insert into spider.alliance_effect(date_time,shop_nick,event_id,pid,channel,uv_num,cart_add_cnt,clt_add_cnt,alipay_num,alipay_amt) value (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
            data = (str(item.get('时间')), str(item.get('商家昵称')), item.get('活动id'), item.get('pid'), item.get('渠道名称'),
                    item.get('进店uv数'), item.get('加购人数'), item.get('收藏人数'), item.get('付款笔数'), item.get('付款金额'))
            db_state = db.execute_data(sql, data)
            succ = db_state.get('succ')
            if succ:
                pass
                # print('{}/{} into db succ'.format(item_id,date_time))
    except Exception as e:
        logger.exception(str(e))
    return succ




def action(event_id, date_time):
    try:
        file_name = "./data/{}-{}.xls".format(event_id, date_time)
        item_list = read_csv(file_name)
        if not item_list:
            logger.info('{},date{} is null'.format(event_id, date_time))
        if item_list:
            succ = insert_into_db(item_list)
            if succ:
                logger.info('insert_db succ {}\{}'.format(event_id, date_time))
    except Exception as e:
        logger.exception(str(e))

# item_datas = select_item_id()


class Base_data():
    def __init__(self):

        self.url_queue = Queue()
        self.content_list_queue = Queue()
        # succ, self.item_datas = select_item_id()
        # succ,self.item_datas = select_item_id()
        # succ,self.item_datas = item_datas

    def get_url_list(self):  # 构造urllist
        # item_datas = select_item_id()

        # for i in self.item_datas:
        for i in item_datas:

            self.url_queue.put(i)


    def parse_url(self):  # 发送请求
        while True:
            item = self.url_queue.get()
            print(item)
            action(item[0], TODAY)

            self.url_queue.task_done()



    def run(self):
        t_list = []

        # 1.构造urllist
        t_url = threading.Thread(target=self.get_url_list)
        t_list.append(t_url)
        for i in range(16):
            t_parse = threading.Thread(target=self.parse_url)
            t_list.append(t_parse)


        for t in t_list:
            t.setDaemon(True)  # setDaemon设置为守护线程，守护线程：就是说当前这个线程重不重要，主线程技术的时候，子线程会立马结束
            t.start()

        for q in [self.url_queue]:
            q.join()  # 等到队列的计数为0的时候，join效果失效，否则主线程会在此等待



# def main():
#     try:
#         succ, item_datas = select_item_id()
#         for item in item_datas:
#             action(item[0], TODAY)
#
#     except Exception as e:
#         logger.exception(str(e))


def  main():
    global item_datas
    succ, item_datas = select_item_id()

    s = time.time()
    base = Base_data()
    DATA_1 = base.run()
    e = time.time()
    print('用时{}'.format(e - s))

if __name__ == '__main__':
    main()
    # s = time.time()
    #
    #
    # base = Base_data()
    # DATA_1 = base.run()
    # e = time.time()
    # print('用时{}'.format(e - s))