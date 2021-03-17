#! /usr/bin/python3
# -*- coding: utf-8 -*-

# pip3 install selenium pyvirtualdisplay
# need package xvbf
# http://www.knight-of-pi.org/python3-browser-tests-on-a-raspberry-pi-with-firefox-virtualdisplay-selenium-and-pytest/
# https://stackoverflow.com/questions/54830544/trying-to-use-selenium-on-a-raspberry-pi2-stretch

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
import selenium.common.exceptions
from pyvirtualdisplay import Display
import time
import random
import urllib
import urllib.request
import urllib.error
import sys

# ========================================================================================================
first_pass = True
uFireFox = True
uChrome  = True
# ========================================================================================================
def println(line):
    #print line.decode('utf-8').encode('cp866')
    print(line)
def printlns(line):
    #print line.decode('utf-8').encode('cp866'),
    print(line, end='')
# ========================================================================================================
# ========================================================================================================

def get_html(url, trains=('059','015'), vtypes=("Плацкарт",), pnum=1, ptypes=('Ниж','Верх'), ptypes_none=('боков','посл'), prefixfile='rzd_'):  

    global uFireFox, uChrome, first_pass
    DoSendSMS = False
    println('Begin: {0}'.format(time.strftime("%d.%m %H:%M:%S", time.localtime())))

    if first_pass: 
        uFireFox = True
        uChrome  = True
        
        println("Поиск поездов: {0}".format(trains))
        println("Тип вагона:    {0}".format(vtypes))
        println("Тип мест:      {0}".format(ptypes))
        println("Исключая тип:  {0}".format(ptypes_none))
        println("Кол-во мест >= {0}".format(pnum))
        if(TEST_MODE): println("TEST_MODE: СМС не посылается")
        else: println("СМС посылается") 
        if(not NO_VISIBLE): println("Браузер открывается")
        else: println("Браузер не открывается") 
        
        if url.find("checkSeats=0"):
            checkSeats = 0
            println('В url-адресе: "Расписание", Ok!')
        else: 
            checkSeats = 1
            println('В url-адресе: "Только с местами" (программа не выполняет контроль корректности запроса, лучше выбрать "Расписание")')
            
        println("\nSelenium =========================================\n---------=========================================")

    if NO_VISIBLE :
        display = Display(visible=0, size=(800, 600))
        display.start()

    if uFireFox:
        if first_pass: printlns("try Firefox()...")
        try:
            driver = webdriver.Firefox()
        except selenium.common.exceptions.WebDriverException as eFF:
            uFireFox = False
            println('Firefox except\n--------------------------------------------')
            println(sys.exc_info())
            println(eFF)

    if not uFireFox and uChrome:
        if first_pass: printlns("try Chrome()...")
        try:
            driver = webdriver.Chrome()
        except selenium.common.exceptions.WebDriverException as eCH:
            uChrome = False
            println('Chrome  except\n--------------------------------------------')
            println(sys.exc_info())
            println(eCH)

    if not uFireFox and not uChrome:
        println('''
--------------------------------------------
          Not run by root !!!!
--------------------------------------------''')
        Send_sms("Webdrvers is excepted! Программа отключилась !!!")
        println('Programm is closed !!!!\n--------------------------------------------')
        exit(0)

    if first_pass: 
        println("\n--------------------------------------------\n")

    #driver.set_page_load_timeout(20)
    driver.get(url)
    #time.sleep(10)
    try:
        WebDriverWait(driver, 20).until(lambda trn : trn.find_elements_by_class_name("route-items-cont"))
    finally:
        pass
    
    html_source = driver.page_source
    F = open(prefixfile+'.html.log', encoding='utf-8', mode="wt"); F.write(html_source); F.close()
    
    All_Train_Find = False
    for TrainS in driver.find_elements_by_class_name("route-items-cont") :
        for train in TrainS.find_elements_by_class_name("route-item__train-info") :
            NumTrainTxt = train.find_element_by_class_name("route-trnum").text
            #==================
            for trn in trains :
                if NumTrainTxt.count(trn) > 0: 
                    All_Train_Find = True
                    break
            else : continue
            #==================
            println('{0} train N {1} '.format(time.strftime("%d.%m %H:%M:%S", time.localtime()),NumTrainTxt))
            
            AllCarType = train.find_element_by_class_name("route-item__car-types")
            if len(AllCarType.text) == 0 :
                println( " МЕСТ НЕТ\r\n")
                continue
            
            for CarType in AllCarType.find_elements_by_class_name("route-carType-item"):
                try:
                    ServCat = CarType.find_element_by_class_name("serv-cat")
                except: 
                    continue
                ServCatText = ServCat.text
                #==================
                for vtp in vtypes :
                    if (vtp == 'All') or (ServCatText.count(vtp) > 0) : break
                else : continue
                #==================
                #println("  {0}".format(ServCatText))
                ServCat.click()
                #time.sleep(10)
                try:
                    WebDriverWait(driver, 20).until(lambda trn : trn.find_elements_by_class_name("route-item__cars-list__item"))
                finally:
                    pass
                    
                for Car in train.find_elements_by_class_name("route-item__cars-list__item"):
                    NumCar = Car.find_element_by_class_name("route-car-num").text
                    print("  Вагон {0}, {1}".format(NumCar,ServCatText))
                    for PClass in Car.find_elements_by_class_name("route-car-seatrow"):
                        #PlaceCntS = PClass.find_element_by_class_name("col-xs-5").text
                        #PlaceCnt  = int(PClass.find_element_by_class_name("col-xs-5").find_element_by_tag_name("b").text)
                        PlaceType = PClass.find_element_by_class_name("col-xs-12").text
                        #println("=    {0}, {1}".format(PlaceType,PlaceCntS))
                        #==================
                        ToNext = True
                        for ptp in ptypes :
                            if (ptp.lower() == 'all') or ((PlaceType.lower()).find(ptp.lower()) >= 0) : 
                                ToNext = False
                                break
                        for ptpn in ptypes_none :    
                            if (PlaceType.lower()).find(ptpn.lower()) >= 0 : 
                                ToNext = True
                                break
                        if ToNext : continue
                        #==================  ptypes=('Нижние'), ptypes_none=('Нижние боковые')
                        PlaceCntS = PClass.find_element_by_class_name("col-xs-5").text
                        PlaceCnt  = int(PClass.find_element_by_class_name("col-xs-5").find_element_by_tag_name("b").text)
                        #=vvvvvvvvvvvvvvvvvvvvvvvvvvvvv
                        if pnum > PlaceCnt : continue
                        #=^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                    
                        PlacePrz  = PClass.find_element_by_class_name("car-type__cost-digit").text.replace('&nbsp;','')
                        DoSendSMS = True
                        println("    {0}, {1}".format(PlaceType,PlaceCntS))

            println("=============================")
                                        
    if not All_Train_Find : 
        printlns("Поезд(а)")
        for trn in trains : 
            printlns(" '{0}' ".format(trn)) 
        println("не найдены")
        if first_pass: 
            if checkSeats == 1 :
                println("Возможно нет билетов. (Контроль корректности не производится) ")
            else :
                println("Некорретный запрос. Указанные поезд(а) не ходят в этот день")
    
    driver.quit()
    if NO_VISIBLE : display.stop()
    first_pass = False
    
    if DoSendSMS :
        #Send_sms("RZD-Finder:  Есть Билеты",("9128569772","9124514161"))
        Send_sms()
        exit(0)
    
    return
#    
#def Send_sms_old(str_out="RZD-Finder:  Есть Билеты".encode('utf-8'), tels =("9128569772",) ):   # str-out in utf-8 codding
#
#    for tel in tels :
#        println("=== sending sms to {0} ===".format(tel))
#        
#        if TEST_MODE : return
#        #  Send by SMS.RU
#        sms_url = 'http://sms.ru/sms/send?api_id=EB7A3F24-D7A8-71D2-727A-27EF3347AA3E&to=7{0}&text={1}'.format(tel,str_out)
#        try:    GIS = urllib.urlopen(sms_url)
#        except: print("ERROR  send  SMS")
#        GIS.close()       

def Send_sms(str_out="RZD-Finder:  Есть Билеты", tels =("9128569772",) ):   # str-out in utf-8 codding

    teltext = ''
    for i in range(len(tels)-1) : teltext += ("7{0},".format(tels[i]))
    teltext += ("7{0}".format(tels[len(tels)-1]))

    println("=== sending sms to {0} ===".format(teltext))
    if TEST_MODE : return

    #  Send by SMS.RU
    sms_url = r'https://sms.ru/sms/send?json=1'
    values = {'msg':str_out,'to':teltext, 'api_id':'EB7A3F24-D7A8-71D2-727A-27EF3347AA3E'}
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii') # data should be bytes        
    req = urllib.request.Request(sms_url, data)
    try:
        respo = urllib.request.urlopen(req)
        println(respo.read())
    except urllib.error.URLError as e: 
        println("========= ERROR  send  SMS ===========")
        println(e.reason)
        println("======================================")
        return 
            

##########################################

url =  'https://pass.rzd.ru/tickets/public/ru?layer_name=e3-route&st0=Сарапул&code0=2060560&dt0=13.03.2021&st1=Москва&code1=2000000&tfl=3&md=0&checkSeats=0'
#url =  'https://pass.rzd.ru/tickets/public/ru?STRUCTURE_ID=704&refererPageId=4819&layer_name=e3-route&tfl=3&st0=%D0%A1%D0%90%D0%A0%D0%90%D0%9F%D0%A3%D0%9B&code0=2060560&dt0=13.09.2020&st1=%D0%9C%D0%9E%D0%A1%D0%9A%D0%92%D0%90&code1=2000000&checkSeats=0'
trains = ("015","059")

#vtypes = ("Плацкарт",)
#vtypes = ("Плацкарт","Купе")
vtypes = ("Купе",)

ptypes=('Ниж','Верх')
#ptypes=('Ниж',)

#ptypes_none=('боков','посл')
ptypes_none=('none',)

# 'Нижнее','Нижнее боковое','Верхнее','Верхнее боковое','Последнее купе, нижнее','Последнее купе, верхнее','Боковое нижнее у туалета','Боковое верхнее у туалета'
TEST_MODE  = True  #True
NO_VISIBLE = True  #True #False

while(1):

    #get_html_1(url, trains=('059','015'), vtypes=("Плацкарт",), pnum=1, ptypes=('Ниж','Верх'), ptypes_none=('боков','посл'), prefixfile='rzd_')

    html_source = get_html(url, trains, vtypes, 2, ptypes, ptypes_none)
    
    if TEST_MODE : exit(0)
    pause = random.randrange(3 * 60, 5 * 60, 1)
    time.sleep(pause)
    
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
