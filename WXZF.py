# -*- coding: utf-8 -*-

#使用方法：
#1：将配置信息配置在WechatPayInfo类中。
#2：调用BisinessPay（需传参）
#3：重构失败（dealWithRequestError）和成功（dealWithRequestSuccess）的情况的处理（可选）



#设置编码
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

#django stuff
from django.shortcuts import render
from django.http import HttpResponse

#xml dealer
import xml.sax
import xml.sax.handler

#md5 need
import hashlib

#pycurl
try:
    import pycurl
    from cStringIO import StringIO
except ImportError:
    pycurl = None

#随机数
import random



#企业付款的调用方法
#需要传入几个参数：
#OrderNumber：订单号
#openid：收款方的openid
#check：是否校验姓名：0为不校验，1弱校验，2为强制校验
#弱校验：若微信用户已绑定身份证则校验，若未绑定则不校验
#强校验：校验微信用户绑定的身份证姓名，若未绑定则无法付款
#name：收款用户姓名，当check为1或2时，需要传此参数
#money：金额，单位为分
#Des；付款描述
#暂时只支持GET
def BisinessPay(request):

    #API地址
    payurl = "https://api.mch.weixin.qq.com/mmpaymkttransfers/promotion/transfers"

    dic = dealWithRequsetData(request)

    #转换好的数据
    formatDataString = formatData(dic)

    #进行请求
    out = postXmlSSL(formatDataString,payurl);

    #对返回结果进行处理
    xh = XMLHandler()
    xml.sax.parseString(out, xh)
    outDic = xh.getDict()

    #对返回结果进行判断，并自定义处理
    return_code = outDic["return_code"]
    if return_code == "SUCCESS":
        dealWithRequestSuccess(outDic)
        return HttpResponse("成功")

    elif return_code == "FAIL":
        dealWithRequestError(outDic)
        return_msg = outDic["return_msg"]
        err_code = outDic["err_code"]
        return HttpResponse("请求失败，错误类型："+err_code+"。错误说明："+return_msg)

#配置信息，商家的一些微信账号的信息，请在这里配置
class WechatPayInfo(object):

    #公众账号appid
    Appid = "wx****************"
    #商户号
    Mchid = "13********"
    #商户密钥Key
    SecretKey = "********************************"
   
    #支付成功异步通知url
    Notify_url = "http://*************"

    #证书路径
    apiclient_key_pem_PATH = "/**********/apiclient_key.pem"
    apiclient_cert_pem_PATH = "/**********/apiclient_cert.pem"

#处理收到的请求信息，包装成字典
def dealWithRequsetData(request):
    dic = {}
    #公众账号appid
    dic["mch_appid"] = WechatPayInfo.Appid
    #商户号
    dic["mchid"] = WechatPayInfo.Mchid
    #设备号
    #dic["device_info"] = "******"
    #随机字符串
    dic["nonce_str"] = createNoncestr()
    #商户订单号
    dic["partner_trade_no"] = request.GET['OrderNumber']

    #用户openid
    dic["openid"] = request.GET['openid']
        
    checknumber = request.GET['check']

    if checknumber == "0":
        #校验用户姓名选项
        dic["check_name"] = "NO_CHECK"
    elif checknumber == "1":
        #校验用户姓名选项
        dic["check_name"] = "OPTION_CHECK"
        #收款用户姓名
        dic["re_user_name"] = request.GET['name']
    elif checknumber == "2":
        #校验用户姓名选项
        dic["check_name"] = "FORCE_CHECK"
        #收款用户姓名
        dic["re_user_name"] = request.GET['name']
    
    #金额
    dic["amount"] = request.GET['money']
    #企业付款描述信息
    dic["desc"] = request.GET['Des']

    #Ip地址
    dic["spbill_create_ip"] = "192.168.1.1"

    return dic

#对请求失败的情况进行自定义处理
def dealWithRequestError(dic):
    #在这里助理失败的情况
    print dic

#对请求成功的情况进行自定义处理
def dealWithRequestSuccess(dic):
    #在这里助理成功的情况
    print dic

#信息格式化
def formatData(dic):

    #排序
    diction = sorted(dic.iteritems(), key=lambda d:d[0], reverse = False )
	
    #拼接成字符串
    stringtoMD5 = ""
    for i in range(0, len(diction)):
        stringtoMD5 = stringtoMD5 + diction[i][0] + "=" + diction[i][1] + "&"
    stringtoMD5  = stringtoMD5 +"key="+ WechatPayInfo.SecretKey

    #转换成xml
    xml = ["<xml>"]
    for i in range(0, len(diction)):
        xml.append("<{0}>{1}</{0}>".format(diction[i][0], diction[i][1]))

    #转换成XML字符串
    xmlstr =  "".join(xml)
    
    #生成签名
    aftermMD5 = md5(stringtoMD5)

    #拼接签名
    xmlstr = xmlstr + "<sign>"+aftermMD5+"</sign>"+"</xml>"

    return xmlstr

#签名
def md5(str):
    m = hashlib.md5()
    m.update(str)
    out = m.hexdigest()
    return out.upper()

#产生随机字符串，不长于32位
def createNoncestr():
    length = 32
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    strs = []
    for x in range(length):
        strs.append(chars[random.randrange(0, len(chars))])
    return "".join(strs)

#使用证书进行Post请求
def postXmlSSL( xml, url, second=30):
    """使用证书"""
    curl = pycurl.Curl()
    curl.setopt(pycurl.SSL_VERIFYHOST, False)
    curl.setopt(pycurl.SSL_VERIFYPEER, False)
        #设置不输出header
    curl.setopt(pycurl.HEADER, False)
        
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.TIMEOUT, second)
        #设置证书
        #使用证书：cert 与 key 分别属于两个.pem文件
        #默认格式为PEM，可以注释
    curl.setopt(pycurl.SSLKEYTYPE, "PEM")
    curl.setopt(pycurl.SSLKEY, WechatPayInfo.apiclient_key_pem_PATH)
    curl.setopt(pycurl.SSLCERTTYPE, "PEM")
    curl.setopt(pycurl.SSLCERT,WechatPayInfo.apiclient_cert_pem_PATH)
        #post提交方式

    curl.setopt(pycurl.POST, True)
    curl.setopt(pycurl.POSTFIELDS, xml)
    buff = StringIO()
    curl.setopt(pycurl.WRITEFUNCTION, buff.write)

    curl.perform()    
    return buff.getvalue()

#处理的XMl格式数据
class XMLHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.buffer = ""
        self.mapping = {}

    def startElement(self, name, attributes):
        self.buffer = ""

    def characters(self, data):
        self.buffer += data

    def endElement(self, name):
        self.mapping[name] = self.buffer

    def getDict(self):
        return self.mapping


#微博：畸形滴小男孩
