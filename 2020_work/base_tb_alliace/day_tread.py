# -*- coding=utf8 -*-
# coding=utf-8
"""手动输入淘宝联盟cookie"""
import logging
import time
import os
import adzone_manage
import event_detail
import event_detail4
import event_effect2
import event_goods
import event_presum
import event_coopinfo
import read_csv
import threading
import event_detail5





def main():
    start_time = time.time()

    print('这是主线程：', threading.current_thread().name)
    thread_list = []

    t1 = threading.Thread(target=event_detail4.main)
    t2 = threading.Thread(target=event_effect2.main)
    # t3 = threading.Thread(target=event_goods.main)
    t4 = threading.Thread(target=event_presum.main)
    t5 = threading.Thread(target=event_detail5.main)

    thread_list.append(t1)
    thread_list.append(t2)
    # thread_list.append(t3)
    thread_list.append(t4)
    thread_list.append(t5)

    for t in thread_list:
        t.setDaemon(True)
        t.start()

    for t in thread_list:
        t.join()

    print('主线程结束了！', threading.current_thread().name)
    print('一共用时：', time.time() - start_time)
if __name__ == '__main__':
    main()
