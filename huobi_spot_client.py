import requests
from requests import Request
from request_manager import RequestManager
import datetime
import hashlib
import time
import random,string
import base64
import hmac
import urllib
import urllib.parse
import json


# 主账户
# Access_Key = '3b26e886-273eb6c6-dab4c45e6f-2edfe'
# Secret_Key =  'd1e36583-4a575e4f-47fea9a1-4cfb0'

# 子账户_test001
Access_Key = 'rfhfg2mkl3-e3652fe2-4cd0ea14-46c88'
Secret_Key =  '83b02bf0-324313d3-6e0f1e3a-7b6d9'
# Z6RBJWAAWLPPKHKB


class Huobi_Spot_Client():

    def __init__(self, Access_Key, Secret_Key, is_proxies = True):
        self.Access_Key = Access_Key
        self.Secret_Key = Secret_Key
        self.is_proxies = is_proxies
        self.BASE_URL = 'https://api.huobi.pro'
        # self.BASE_URL = 'https://api-aws.huobi.pro'

        self.spot_account_id = 0
        self.margin_account_id = 0
        self.otc_account_id = 0
        self.super_margin_account_id = 0

        self.account_id = self.get_account_id()['data']
        for i in range(len(self.account_id)):
            if self.account_id[i]['type'] == 'spot':
                self.spot_account_id = self.account_id[i]['id']
            elif self.account_id[i]['type'] == 'margin':
                self.margin_account_id = self.account_id[i]['id']
            elif self.account_id[i]['type'] == 'otc':
                self.otc_account_id = self.account_id[i]['id']
            elif self.account_id[i]['type'] == 'super-margin':
                self.super_margin_account_id = self.account_id[i]['id']

        # print('现货账户',self.spot_account_id)
        # print('逐仓杠杆账户',self.margin_account_id)
        # print('OTC 账户',self.otc_account_id)
        # print('super-margin账户',self.super_margin_account_id)

    def utc_now(self):
        return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')

    def generate_signature(self, method, params, request_path):

        if request_path.startswith("http://") or request_path.startswith("https://"):
            host_url = urllib.parse.urlparse(request_path).hostname.lower()
            request_path = '/' + '/'.join(request_path.split('/')[3:])
        else:
            host_url = urllib.parse.urlparse(self.BASE_URL).hostname.lower()
        sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)

        payload = [method, host_url, request_path, encode_params]
        payload = "\n".join(payload)
        payload = payload.encode()

        secret_key = self.Secret_Key.encode()
        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        # signature = signature.decode()
        return signature

    '''账户信息'''
    def get_account_id(self):
        method = 'GET'
        path = '/v1/account/accounts'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }

        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=url,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    def get_account_balance(self):
        account_id = self.spot_account_id
        method = 'GET'
        path = '/v1/account/accounts/'+ str(account_id)+'/balance'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }

        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)


        my_request = Request(
            method=method,
            url=url,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    '''行情数据'''

    def get_k_lines(self, symbol, period):
        method = 'GET'
        path = '/market/history/kline'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }

        params['symbol'] = symbol
        params['period'] = period

        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    def get_ticker(self, symbol):
        method = 'GET'
        path = '/market/detail/merged'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['symbol'] = symbol
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    def get_symbols(self):
        method = 'GET'
        path = '/v1/common/symbols'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }

        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    '''订单类'''
    # 市价买单amount为订单交易额 市价卖单amount为数量
    def create_order(self,symbol,type,amount,price=None,stopprice=None,operator=None):
        account_id = self.spot_account_id
        method = 'POST'
        path = '/v1/order/orders/place'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {}
        data['account-id'] = account_id
        data['symbol'] = symbol
        data['type'] = type
        data['amount'] = amount
        data['price'] = price
        data['stop-price'] = stopprice
        data['operator'] = operator
        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 查询当前未成交订单
    def get_open_orders(self,symbol):
        account_id = self.spot_account_id
        method = 'GET'
        path = '/v1/order/openOrders'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['account-id'] = account_id
        params['symbol'] = symbol
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 基于order_id进行撤单
    def cancel_order_by_id(self,order_id):
        method = 'POST'
        path = '/v1/order/orders/'+order_id+'/submitcancel'
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)
        my_request = Request(
            method=method,
            url=url,
            # data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 搜索历史订单
    # submitted已提交, partial - filled部分成交, partial - canceled, 部分成交撤销, filled,完全成交, canceled, 已撤销，created
    def get_history_orders(self,symbol,state,start_time=None):
        method = 'GET'
        path = '/v1/order/orders'
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['symbol'] = symbol
        params['states'] = state
        if start_time != None:
            params['start-time'] = start_time
        # params['start-time'] = start_time
        # params['end-time'] = end_time

        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 取消所有订单
    def cancel_order_all(self,symbol):
        aa = self.get_open_orders(symbol)
        for i in range(len(aa['data'])):
            self.cancel_order_by_id(order_id=str(aa['data'][i]['id']))

    def apply_borrow_money(self, symbol, currency, amount):
        method = "POST"
        path = "/v1/margin/orders"
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }

        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)


        data = {
            'symbol': symbol,
            'currency': currency,
            'amount': amount,
        }

        data = json.dumps(data)

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)





if __name__ == '__main__':

    aa = Huobi_Spot_Client(Access_Key=Access_Key, Secret_Key=Secret_Key)
    # print(aa.get_account_id())

    # print(aa.get_account_balance())
    '''交易类'''
    # print(int(round(time.time() * 1000)))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit',amount='2.5',price= '2'))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit', amount='2.5', price='2'))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit', amount='2.5', price='2'))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit', amount='2.5', price='2'))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit', amount='2.5', price='2'))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit',amount='2.5',price= '2'))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit',amount='2.5',price= '2'))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit', amount='2.5', price='2'))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit', amount='2.5', price='2'))
    # print(aa.cancel_order_all(symbol='eosusdt'))






    # print(aa.create_order(symbol='eosusdt', type='sell-market', amount='3.8102'))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit', amount='3.0', price='2')['data'])
    # print(aa.get_open_orders(symbol='eosusdt')['data'])
    # print(aa.get_open_orders(symbol='eosusdt'))
    # print(aa.cancel_order_by_id(order_id='62680134237520'))
    # aa.cancel_order_all(symbol='btcusdt')
    #
    # print(aa.get_history_orders(symbol='btcusdt',state='filled'))



    # print(aa.apply_borrow_money(symbol='eosusdt', currency="btc", amount="0.0000000002"))

    # print(aa.get_k_lines(symbol='btcusdt',period='5min'))
    # print(aa.get_ticker(symbol='btcusdt')['tick']['close'])
    # print(aa.get_symbols())

    bb= aa.create_order(symbol='eosusdt', type='buy-limit', amount='3.0', price='2')['data']
    time.sleep(10)
    aa.cancel_order_by_id(order_id=str(bb))

# {'status': 'ok', 'data': '62679572143016'}