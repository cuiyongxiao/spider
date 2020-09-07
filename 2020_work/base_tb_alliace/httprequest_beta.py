#coding=utf-8
"""
http request 
user requests 
access network can use cookie and user_agent
"""
import requests
import logging
import traceback

requests.packages.urllib3.disable_warnings()

logger=logging.getLogger("log")
cookies = [""]
proxy_port=0
user_agenet = [""]
#proxies = {"https": "socks5h://127.0.0.1:"+str(port)}


def query_request(url, method="get", **q_params):
    """
    请求网络
    :param url:  访问url 
    :param method:  获取get 或者 post
    :param q_params:  request里的参数
    :return: 
    """
    succ = False
    info = None
    rep=None
    try:
        if url is None or url == "" or not str(url).startswith("http"):
            return (False, "URLERROR");
        logger.info("===========>:url:"+str(url))

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-encoding": "gzip, deflate,br",
            "accept-language": "zh-CN,zh;q=0.8",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36",
            "upgrade-insecure-requests":"1"
        }

        q_params = q_params if q_params else {}
        q_header = q_params.get("headers")

        headers.update(q_header) if q_header else headers
        q_params["headers"] = headers
        q_params["timeout"] = (3, 3)

        logger.info("<run>:"+str(url))
        rep=None
        if method.upper() == "get".upper():
            rep = requests.get(url=url, **q_params)
        else:
            rep = requests.post(url=url, **q_params)
        code = rep.status_code
        if code == 200:
            logger.info(":succ:")
        rep.encoding = rep.apparent_encoding
        info = rep.text
        if info:
            succ = True
    except Exception as e:
        logger.exception(str(e))
        info = str(e.args[0])
    finally:
        if rep:
            rep.close()
    return succ, info


def query_request_bytes(url,method="get",filename="./data/demo.txt",**q_params):
    """
    请求网络
    :param url:  访问url 
    :param method:  获取get 或者 post
    :param q_params:  request里的参数
    :return: 
    """
    succ = False
    info = None
    rep=None
    try:
        if url is None or url == "" or not str(url).startswith("http"):
            return (False, "URLERROR");
        logger.info("===========>:url:"+str(url))
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-encoding": "gzip, deflate,br",
            "accept-language": "zh-CN,zh;q=0.8",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36",
            "upgrade-insecure-requests":"1"
        }
        q_params = q_params if q_params else {}
        q_header = q_params.get("headers")

        headers.update(q_header) if q_header else headers
        q_params["headers"] = headers
        q_params["timeout"] = (7, 7)

        logger.info("<run>:"+str(url))
        rep=None
        if method.upper() == "get".upper():
            rep = requests.get(url=url, **q_params)
        else:
            rep = requests.post(url=url, **q_params)
        code = rep.status_code
        logger.info("code:"+str(code))
        if code == 200:
            succ = True
            logger.info(url+":succ:")
        # query_data-type: application/vnd.ms-excel;charset=GBK
        content_type = rep.headers.get("query_data-type")
        if content_type == "application/vnd.ms-excel;charset=GBK":
            fp = open(filename, "wb")
            fp.write(rep.content)
            fp.close()
        else:
            rep.encoding = rep.apparent_encoding
            info = rep.text
    except Exception as e:
        logger.exception(str(e))
        info = str(e.args[0])
    finally:
        if rep:
            rep.close()
    return succ, info


session=requests.session()

def query_request_session(url):
    succ=False
    data=None
    rep=None
    try:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-encoding": "gzip, deflate,br",
            "accept-language": "zh-CN,zh;q=0.8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36",
        }
        rep = session.get(url,headers=headers)
        text=rep.text
        code=rep.status_code
        logger.info(str(url)+":url:"+str(code))
        if text:
            data=text
            succ=True
    except Exception as e:
        logger.exception(str(e))
    finally:
        if rep:
            rep.close()
    return succ,data

def get_strem_by_url(url,file):
    """
    访问url 获取流
    :param url:  访问url
    :param file: 存指定的流
    :return: 
    """
    try:
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.8",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36",

        }
        rep = requests.get(url=url, headers=headers, timeout=10,stream=True)
        with open(file,'wb') as f:
            for chunk in rep:
                f.write(chunk)
    except Exception as e:
        print(e)

if __name__=="__main__":
     data = dict()
     data["namw"] = 1
     data["namw1"] = 1

     data=[data_one for data_one in data.items() if data_one[0]=='namw' ]
     print(data)









