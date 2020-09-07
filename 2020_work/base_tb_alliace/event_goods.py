# coding=utf-8
"""每天更新任务 淘宝商品"""
import logging
import time
import datetime
from lxml import etree
from emailsend import MailSend
import hashlib
import json
import requests
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

# H5_ITEM_URL = 'http://h5api.m.taobao.com/h5/mtop.taobao.detail.getdetail/6.0/?jsv=2.4.8&appKey=12574478&t=1523866479863&sign=707adb0aa140b673559049741eebbc2a&api=mtop.taobao.detail.getdetail&v=6.0&ttid=2016%40taobao_h5_2.0.0&isSec=0&ecode=0&AntiFlood=true&AntiCreep=true&H5Request=true&type=jsonp&dataType=jsonp&callback=mtopjsonp1&data=%7B%22exParams%22%3A%22%7B%5C%22id%5C%22%3A%5C%22{}%5C%22%7D%22%2C%22itemNumId%22%3A%22{}%22%7D'
H5_ITEM_URL = 'https://h5api.m.taobao.com/h5/mtop.taobao.detail.getdetail/6.0/?data=%7B%22id%22%3A%22{}%22%2C%22itemNumId%22%3A%22{}%22%2C%22exParams%22%3A%22%7B%5C%22id%5C%22%3A%5C%22{}%5C%22%7D%22%2C%22detail_v%22%3A%228.0.0%22%2C%22utdid%22%3A%221%22%7D'

TODAY = time.strftime('%Y.%m.%d', time.localtime(time.time()))
LAST_MONTH=time.strftime('%Y.%m.%d',time.localtime(time.time()-2592000))
YEAR = datetime.datetime.now().year
# cookie = "thw=cn; cna=BwAdE9rBvVMCAXygHkJRwLBg; t=2b8b24abc9dc66117ad4243f5746ec4b; hng=CN%7Czh-CN%7CCNY%7C156; UM_distinctid=1622cd9d1ec5a7-07b3957eb3dd69-32637b05-fa000-1622cd9d1ed42; miid=726692841672529847; tg=0; enc=3XMijwAmxCr1VClBz7qPLnU0DUnoUTNL3Fpj2L8vjGKo17nsPnbxcO1T3XVq68vUin8BHERJG7zvt3RCNemD7g%3D%3D; cookie2=2a7d5e382f206557c80afa30517d680f; _tb_token_=3e663e7f50e6; l=Ap-foJBcX5TqZ/4OlCHwTiiEr/gpA/Om; tk_trace=oTRxOWSBNwn9dPyorMJE%2FoPdY8zfvmw%2Fq5hiWqyZG2%2BvZc%2BwrkY9viHpaytWoI4AWS3Ma8rwFDBZE9oDZUqtWNowCot1frjrlA%2BUgqwy96qbdEm7C4xS0CzBzR7Iq1CMmgP4TsnEVBMMOfpb2nWBruM7l4J8odKmzigtEuO9jLrHOw3tNl0laRBNhPh9%2BmO3yZhCtX3JpnhqJHwu147UOEZm8rLyKW2S%2BL3JHLp2qWJKT8c4yvwyhF5k5Zwk5ZsAiu8jUTZjPfL7e%2FUXWBZAoz6h5cfLJTet6noSC%2FMu53QHMLBTWKOhxnfG93XzRp%2FJvAtEX7pcUB5JRQcI6900ngSrfHMdvMg5mZoclScSLSadctQCAWZFBZE3oAf970fbuCL8Drmk%2F%2FtF4WCkOn7Zre815e6%2FRrcCsjZo0260rrHQrUlptKFNXVAoLmXEWbAuOl2HyA%2BoE4DMHQuL%2BHoW8F4djZRYG62XSSaYe7%2BCvh4KkPzbfQ2pEYXBoXo5xo2naOSbJSVzwWcgeZWIh6NGGTvyOcJWhO48yA6Bpfw8UikJzdZQtobrD9JQsVIL%2BdFrOOg1vKPnM6zHSODx; _m_h5_tk=8819f3c35e069d1c2d8711d1c91bfdae_1534158164989; _m_h5_tk_enc=644153eb37e5e72d98f62c88f96347e8; mt=ci=0_0; v=0; ockeqeudmj=l95tFww%3D; munb=3459155204; WAPFDFDTGFG=%2B4cMKKP%2B8PI%2Buj7Rag0wBnbXolTcpkQQZJ3WvbI%3D; _w_app_lg=0; unb=3459155204; sg=%E6%B2%AB47; _l_g_=Ug%3D%3D; skt=e679d22dbc1acbb1; uc1=cookie21=U%2BGCWk%2F7oPGl&cookie15=Vq8l%2BKCLz3%2F65A%3D%3D&cookie14=UoTfL8uAK%2FoPYg%3D%3D; cookie1=VyzFjJf%2F1po3qax99Hxz7oaBLf0a00o%2FRf9cWb%2BA3Us%3D; csg=88544242; uc3=vt3=F8dBzrpF%2BuwsfL0rSuY%3D&id2=UNQyS9x4Nb1yXQ%3D%3D&nk2=1w1%2Bj0VttMUYUiWB&lg2=V32FPkk%2Fw0dUvg%3D%3D; tracknick=%5Cu6233%5Cu7834%5Cu4E2A%5Cu5C0F%5Cu6CE1%5Cu6CAB; lgc=%5Cu6233%5Cu7834%5Cu4E2A%5Cu5C0F%5Cu6CE1%5Cu6CAB; _cc_=Vq8l%2BKCLiw%3D%3D; dnk=%5Cu6233%5Cu7834%5Cu4E2A%5Cu5C0F%5Cu6CE1%5Cu6CAB; _nk_=%5Cu6233%5Cu7834%5Cu4E2A%5Cu5C0F%5Cu6CE1%5Cu6CAB; cookie17=UNQyS9x4Nb1yXQ%3D%3D; ntm=1; linezing_session=8XGF5BcKjQm6cZpyX2eYOEsj_1534148184789yyxD_37; isg=BJubrqpTRFOn7bj-tcY3O-HFKvnF2KWv_gy_cI3YdxqxbLtOFUA_wrnuAsJi1wdq"
cookie = ""


# 获取数据库里所有的已经有的item_id
def select_db_shops():
    succ = False
    datas = list()
    try:
        sql = "select shop_id,shop_name,h5_url,seller_id from ruhnn_crawler.contend_shopinfo where shop_id not in (select distinct(s.shop_id) from ruhnn_crawler.contend_shopinfo s left join ruhnn_crawler.contend_fans f on s.shop_id=f.shop_id where s.kind = 0 and s.invalid =1 and date(f.created_at) = date_sub(curdate(),interval 0 day)) and kind = 0 and invalid =1;"
        db_stat = db.execute_data(sql)
        succ = db_stat.get("succ")
        if not succ:
            return False
        datas = db_stat.get("data")
    except Exception as e:
        logger.exception(str(e))
    logger.info("now db has shops len:" + str(len(datas)))
    return succ, datas


def send_email(subject, to_email, message):
    succ_send = False
    try:
        succ_send = MailSend().send_email_simple_ssl(subject, to_email, message)
    except Exception as e:
        logger.exception(str(e))
    return succ_send


def send_email_warning(message):
    subject = "淘宝联盟-邮件"
    fail_email_accpeter = ['wechat13144@163.com']
    succ_send = send_email(subject, to_email=fail_email_accpeter, message=message)
    logger.info("send_succ" + str(succ_send))


# 获取数据库里所有的已经有的item_id
def select_db_url():
    succ = False
    datas = list()
    try:
        sql = "select shop_id,shop_name,url from ruhnn_crawler.contend_shopinfo where h5_url is null and invalid =1 and kind=0;"
        db_stat = db.execute_data(sql)
        succ = db_stat.get("succ")
        if not succ:
            return False
        datas = db_stat.get("data")
    except Exception as e:
        logger.exception(str(e))
    logger.info("now db has shops len:" + str(len(datas)))
    time.sleep(5)
    return succ, datas


def get_itempage_from_chrome(url):
    global driver
    page = None
    try:
        driver.get(url)
        print('time sleep 10s')
        time.sleep(10)
        page = driver.page_source

    except Exception as e:
        logger.exception(str(e))
    return page


def update_task_list(event_id):
    succ = False
    try:
        sql = "update spider.alliance_task_list set shop_status =1 where event_id ={};".format(event_id)
        db_state = db.execute_data(sql)
        succ = db_state.get("succ")
    except Exception as e:
        logger.exception(str(e))
    return succ


def insert_into_db(data_dict,event_id,item_id):
    succ = False
    try:
        shop_id = data_dict.get('shop_id')
        shop_name = data_dict.get('shop_name')
        quantity = data_dict.get('quantity')
        real_price = data_dict.get('real_price')
        presell=data_dict.get('pre_sell')
        sql = 'update spider.alliance_goods set shop_id=%s,shop_name=%s,quantity=%s,real_price=%s,presell_time=%s where event_id=%s and item_id=%s;'
        data =(shop_id,shop_name,quantity,real_price,presell,event_id,item_id)
        db_state = db.execute_data(sql, data)
        succ = db_state.get("succ")
        if succ:
            print('event_id {} goods succ'.format(event_id))
    except Exception as e:
        logger.exception(str(e))
    return succ


def get_js(token, data, t):
    try:
        data_str = json.dumps(data)
        str_ = token + '&' + t + '&12574478&' + data_str
        hl = hashlib.md5()
        hl.update(str_.encode(encoding='utf-8'))
        sign = hl.hexdigest()
        return sign
    except Exception as e:
        logger.exception(str(e))


def get_data_by_re(page, express):
    """
    通过正则匹配内容
    :param page:
    :param express:
    :return:
    """
    succ = False
    result = ""
    error_message = 'get_data_by_re error >> {0}'

    try:
        comp = re.compile(r'{0}'.format(express), re.S)
        result = comp.findall(page)
        succ = True
    except Exception as e:
        print(str(e))
        result = error_message.format(express)
        traceback.print_exc()
    return succ, result


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


def requests_taobao(item_id,proxies):
    succ = False
    info = None
    try:
        q_params = dict()
        url = H5_ITEM_URL.format(item_id,item_id,item_id)
        headers={"user-agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"}
        """
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
                   "user-agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"
                   "x-requested-with": "XMLHttpRequest"
                   }
        params = {"eventId": event_id,
                  "spm":"a219t.7900221.0.0.71c575a53UMYBR",
                  "shopKeeperId": shop_keeper_id,
                  "downloadId": "DOWNLOAD_REPORT_EFFECT_DETAIL",
                  "startTime": LAST_MONTH,
                  "endTime": TODAY
                  }
        """
        # "itemName":"张大奕辛普森工装羽绒服女短款2018新款白鹅绒时尚情侣加厚羽绒衣"}
        q_params['proxies'] = proxies
        q_params['headers'] = headers
        q_params["timeout"] = (2, 4)
        # q_params['params'] = params

        # filename = "./data/" + "{}-{}".format(event_id,TODAY) + ".xls"
        # succ, info = query_request(url, **q_params)
        rep = requests.get(url=url, **q_params)
        code = rep.status_code
        if code == 200:
            logger.info(":succ:")
        rep.encoding = 'utf-8'
        info = rep.text
        if info:
            succ=True
        # succ, info = query_request_bytes(url,filename=filename, **q_params)
    except Exception as e:
        logger.info(str(e))
    return succ, info


def get_data_by_xpath(page, express, extra_express=None):
    """
       用xpath解析网页
       :param page:
       :param express:
       :param extra_press:
       :return: result
    """
    result = ""
    error_message = 'get_data_by_xpath error >> {0}'
    succ = False
    try:
        selector = etree.HTML(page)
        page = selector.xpath(express)
        if extra_express:
            page = [p.xpath(extra_express) for p in page] if page else None
        result = page
        succ = True
    except Exception as e:
        print(str(e))
        result = error_message.format(express)
        traceback.print_exc()
    return succ, result


def analyzer_info(info):
    """解析任务列表页信息"""
    result = dict()
    item_list = list()
    shop_name = None
    pre_sell=None
    shop_id=None
    quantity=None
    real_price=None
    try:
        data_dict=dict()
        j_info = json.loads(re.match(".*?({.*}).*", info, re.S).group(1))
        shop_info = j_info.get('data').get('seller')
        if shop_info:
            data_dict['shop_id'] = shop_info.get('shopId')
            data_dict['shop_name'] = shop_info.get('shopName')
        data = j_info.get('data').get('apiStack')
        result = data[0].get('value')
        re_info = json.loads(result)
        data_dict['quantity'] = re_info.get('skuCore').get('sku2info').get('0').get('quantity')
        data_dict['real_price'] = re_info.get('skuCore').get('sku2info').get('0').get('price').get('priceText')
        pre_presell_list = re_info.get('skuBase')
        if pre_presell_list:
            presell_list=pre_presell_list.get('props')[0]
            if presell_list:
                presell=presell_list.get('values')[0].get('name')
                if presell.endswith('发货'):
                    dig_list=re.findall(r"\d+\.?\d*",presell)
                    data_dict['pre_sell']="{}-{}-{}".format(YEAR,dig_list[-2],dig_list[-1])
        # total_page=data.get('totalPages')
    except Exception as e:
        logger.info(str(e))
    return data_dict


def struct_info(result):
    try:
        live_id = result.get('liveId')
        room_num = result.get('broadCaster').get('roomNum')

    except Exception as e:
        logger.error(str(e))
    return live_id, room_num


def init_brower():
    succ = False
    global driver
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        driver_path = config.get("driver")
        chrome_plugin = config.get("chrome_plugin")
        driver_path = "/usr/local/bin/chromedriver"
        logger.info("driver_path:" + str(driver_path))
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        # chrome_options.add_extension(chrome_plugin)
        chrome_options.add_argument('lang=zh_CN.UTF-8')
        # chrome_options.add_argument('test-type')
        # chrome_options.add_argument('--disable-gpu')
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument('--proxy-server=https://{}:{}'.format(ip,port))
        # chrome_options.add_argument('user-agent="Mozilla/5.0 (iPod; U; CPU iPhone OS 2_1 like Mac OS X; ja-jp) AppleWebKit/525.18.1 (KHTML, like Gecko) Version/3.1.1 Mobile/5F137 Safari/525.20"')
        driver = webdriver.Chrome(executable_path=driver_path, chrome_options=chrome_options)
        succ = True
    except Exception as e:
        logger.exception(str(e))
    return succ


def sycm_login():
    try:
        user_name = '裙子卖掉了:技术'
        password = 'qunzi123456'
        global driver
        succ = init_brower()
        if succ:
            # driver.get('https://sycm.taobao.com/custom/login.htm?_target=http://sycm.taobao.com/portal/home.htm')
            driver.get(
                'https://login.taobao.com/member/login.jhtml?from=sycm&full_redirect=true&style=minisimple&minititle=&minipara=0,0,0&sub=true&redirect_url=http://sycm.taobao.com/portal/home.htm')
            time.sleep(2)
            # driver.maximize_window()
            user = driver.find_element_by_xpath("//*[@id='TPL_username_1']");
            user.send_keys(user_name)

            # driver.switch_to_input('TPL_username_1')
            # time.sleep(2)
            # driver.find_element_by_id('TPL_password_1').send_keys(u'qunzi123456')
            pw = driver.find_element_by_xpath("//*[@id='TPL_password_1']");
            for i in password:
                time.sleep(random.random())
                pw.send_keys(i)
            time.sleep(2)
            driver.find_element_by_id('J_SubmitStatic').click()
    except Exception as e:
        print(str(e))


def update_goods_status(event_id):
    succ=False
    try:
        sql = "update spider.alliance_task_list set goods_status=1 where event_id={};".format(event_id)
        db_state =db.execute_data(sql)
        succ=db_state.get("succ")
    except Exception as e:
        logger.exception(str(e))
    return succ

def action(event_id, item_id):
    try:
        succ_proxy, proxy_list = sql_select_port()
        if not succ_proxy:
            logger.info("proxy get fail")
            return
        proxies = get_proxy(proxy_list)
        # cookie=sycm_login()

        succ, info = requests_taobao(item_id, proxies)
        if succ :
            data_dict = analyzer_info(info)
            # if not result:
            #     pass
                # print('邮件报警')
                # message = '淘宝联盟任务详情event_effect数据为空'
                # send_email_warning(message)
            # if result:

            succ = insert_into_db(data_dict,event_id,item_id)
            if succ:
                update_goods_status(event_id)
        if not succ:
            logger.info('fail event_goods date{}'.format(TODAY))
                # succ = update_shop_status(item_id)
                # if not succ:
                #     logger.info('update shop_status fail item_id{}'.format(item_id))
    except Exception as e:
        logger.error(str(e))

def select_alliance_detail():
    succ = False
    datas = list()
    try:
        sql = "select event_id from spider.alliance_detail;"
        db_stat = db.execute_data(sql)
        succ = db_stat.get("succ")
        if not succ:
            return False
        datas = db_stat.get("data")
    except Exception as e:
        logger.exception(str(e))
    # logger.info("now db has shops len:" + str(len(datas)))
    return succ, datas



def select_item_id():
    succ = False
    datas = list()
    try:
        sql="select g.event_id,g.item_id from spider.alliance_goods g join spider.alliance_task_list l on g.event_id=l.event_id where l.shop_status=0 and l.goods_status=0;"
        # sql = "select event_id,shop_keeper_id from spider.alliance_task_list where shop_status=0 and effect_status=0 and status in (3,4,5);"
        db_stat = db.execute_data(sql)
        succ = db_stat.get("succ")
        if not succ:
            return False
        datas = db_stat.get("data")
    except Exception as e:
        logger.exception(str(e))
    logger.info("now db has shops len:" + str(len(datas)))
    return succ, datas


def get_cookie():
    with open('./cookie.txt', 'r') as f:
        cookie = f.read()
        f.close()
    return cookie


def main():
    try:
        # cookie = get_cookie()
        # cookie="t=feeb533c4eef3611443b05adf9472aa7; cna=BwAdE9rBvVMCAXygHkJRwLBg; _umdata=A502B1276E6D5FEF275D1CD1A8E9E0B7B85291F3F6F058388A85BFACD7ECF99FC2D0737F79F86CF9CD43AD3E795C914CEA49F819C08F917023EC3CC5D95013A2; cookie2=1a83921a41174d7dacade8e754c1e15e; v=0; _tb_token_=736e887888b83; alimamapwag=TW96aWxsYS81LjAgKE1hY2ludG9zaDsgSW50ZWwgTWFjIE9TIFggMTBfMTJfNikgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzcxLjAuMzU3OC45OCBTYWZhcmkvNTM3LjM2; cookie32=ea7fe24eef16456f9e3376986889976d; alimamapw=FyYIFCAmFSZ4FHFwRnFwRnYmA1MPOFFWVFAPUAMEU1EEVApXUQIIUlJUA1dbAAMCBQcAB1YH; cookie31=MTMwMjk0NDMzLCVFNyU4OCVCMSVFNyVCQSVBMiVFNyVCQSVBMjE3NywzNTE2ODc2MjgzQGFsaW1hbWEuY29tLFRC; taokeisb2c=; login=Vq8l%2BKCLz3%2F65A%3D%3D; rurl=aHR0cDovL3d3dy5hbGltYW1hLmNvbS9pbmRleC5odG0%3D; isg=BMrKoZBgomMPJShRfq6vw4PRG7asE0TIZKxO7FQDdp2oB2rBPEueJRB1Fzt-7Mat; l=bBOt_n9PvF68jrASBOCanurza77OSIRYYuPzaNbMi_5dN6TsGeQOluksZF96Vf5RsUTB4RONxuJ9-etXZ"
        # action(cookie)
        """
        succ, item_datas = select_item_id()
        succ, event_datas = select_alliance_detail()
        event_list=list()
        for event_id in event_datas:
            event_list.append(event_id[0])
        for item in item_datas:
            if item[0] not in event_list:
                action(item[0], item[1], cookie, item[2])
        """
        for _ in range(10):
            succ, item_datas = select_item_id()
            if not item_datas:
                print('event_goods succ')
                break
            for item in item_datas:
                #time.sleep(0.4)
                action(item[0], item[1])
    except Exception as e:
        logger.error(str(e))


if __name__ == '__main__':
    log_file = config.get("log_dir_taobao") + "goods"
    initlog_file(filename=log_file, file_allow=True)
    # shopinfo_action()
    main()
    # 定时操作，每小时运行一次
    
    sched = BackgroundScheduler()

    sched.add_job(main, 'cron', hour='9',minute='3',second='0',max_instances=5)
    # sched.add_job(action, 'interval',seconds=10,id="cron_task")
    try:
        sched.start()
    except Exception as e:
        print(str(e))

    while True:
        time.sleep(10)
    
