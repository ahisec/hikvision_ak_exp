
import base64
import json
import time
import uuid
import hmac 
import hashlib
import requests
import urllib3
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Hik():
    ### 海康威视

    def __init__(self,base_url,appKey,appSecret):
        self.base_url = base_url
        self.appKey = appKey
        self.appSecret = appSecret


    # 获取监控点资源
    def get_cameras(self):
        url =  "/api/resource/v1/cameras"

        body = {
        "pageNo": 1,
        "pageSize":1000
    }
        results = self.hik_post(url,json.dumps(body))
        return results


    def exp(self):
        results = self.get_cameras()
        for item in results.get('data').get('list'):
            data =  {
                    'cameraName':item.get('cameraName'),
                    'cameraIndexCode':item.get('cameraIndexCode'),
                    'regionIndexCode':item.get('regionIndexCode'),
                    'createTime':item.get('createTime'),
                    'updateTime':item.get('updateTime'),
                    'priviewurls':self.get_previewurls(item.get('cameraIndexCode')),
                    'online':self.get_camera_online(item.get('cameraIndexCode'))

                }
            print(data)            
            save_result('hik_res.txt',data)      


    # 获取监控预览
    def get_previewurls(self,cameraIndexCode,protocol='rtsp'):
        url =  "/api/video/v2/cameras/previewURLs"
        body = {
            "cameraIndexCode": cameraIndexCode,
            "streamType": 0, 
            "protocol": protocol,
            "transmode": 1,    
        }

        results = self.hik_post(url,json.dumps(body))

        return results.get('data').get('url')


    # 获取监控点在线状态
    def get_camera_online(self,cameraIndexCode):
        url =  "/api/nms/v1/online/camera/get"
        body = {
            "indexCodes": [
                cameraIndexCode
            ],
        }

        results = self.hik_post(url,json.dumps(body))
        if(str(results.get('data').get('list')[0].get('online')) == '1'):
            return '在线'
        else:
            return '离线'
        

    # 签名摘要
    def sign(self,key, value):
        temp = hmac.new(key.encode(), value.encode(), digestmod=hashlib.sha256)
        return base64.b64encode(temp.digest()).decode()
    
    


    # 发送请求封装
    def hik_post(self,api_url,data):

        api_url = '/artemis'+ api_url
        x_ca_nonce = str(uuid.uuid4())
        x_ca_timestamp = str(int(round(time.time()) * 1000))
        sign_str = "POST\n*/*\napplication/json" + "\nx-ca-key:" + self.appKey + "\nx-ca-nonce:" + \
                x_ca_nonce + "\nx-ca-timestamp:" + x_ca_timestamp + "\n" + \
                api_url
        
        signature = self.sign(self.appSecret, sign_str)

        headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "x-ca-key": self.appKey,
        "x-ca-signature-headers": "x-ca-key,x-ca-nonce,x-ca-timestamp",
        "x-ca-signature": signature, 
        "x-ca-timestamp": x_ca_timestamp,
        "x-ca-nonce": x_ca_nonce
    }
        
        
        results = requests.post(self.base_url + api_url, data, headers=headers,  verify=False)
        # print(results)
        if(str(results.json().get('code')) == '0' and "succe" in results.json().get('msg')):
            return results.json()
        else:
            print('request_error:' + results.json().get('msg'))
            exit()


#### 萤石云
class Ys():

    accessToken = None
    def __init__(self,appKey,appSecret):
        self.banner()
        self.appKey =  appKey
        self.appSecret = appSecret
        self.get_accesstoken()

    def banner(self):
        print("\n\n\n\n")
        print("视频预览播放地址参考:https://github.com/Ezviz-OpenBiz/EZUIKit-JavaScript-npm/tree/master")
        print("\n\n\n\n")
    # 获取accesstoken
    def get_accesstoken(self):

        try:
            with open('ys_accesstoken.txt','r') as f:
                    content = json.loads(f.read())
                    if(time.time() < int(content.get('data').get('expireTime'))):
                        self.accessToken = content.get('data').get('accessToken')
                        print('已从txt中获取到accesstoken')                           
                    else:
                        print('accesstoken已过期,重新获取')
                        self.request_accesstoken()
        except:
            self.request_accesstoken()
        

    # 请求accesstoken
    def request_accesstoken(self):
        url = "https://open.ys7.com/api/lapp/token/get"
        data = {
            "appKey":self.appKey,
            "appSecret":self.appSecret
            }
            
        results = requests.post(url,data)

        if(str(results.json().get('code')) == '200'):
            #将获取到的token写入到文件中
            self.accessToken = results.json().get('data').get('accessToken')
            with open('ys_accesstoken.txt', 'w') as f:
                f.write(json.dumps(results.json()))
            print('已保存accesstoken到文件')
        else:
            print(results.json().get('msg'))
            exit()

    # 获取设备列表
    def get_devices(self):
        url = '/api/lapp/device/list'
        body = {
            'accessToken':self.accessToken,
            'pageStart':0,
            'pageSize':2
        }
        results = self.post(url,body)
        # print(results)
        return results.get('data')

    # 获取播放地址
    def get_live(self,deviceSerial):
        url = '/api/lapp/v2/live/address/get'
        body = {
            'accessToken':self.accessToken,
            'deviceSerial':deviceSerial
        }   
        results = self.post(url,body)
        # print(results.get('data').get('url'))
        return results.get('data').get('url')

    def exp(self):
        results = self.get_devices()
        for item in results:
            data = {
                'deviceName':item.get('deviceName'),
                'deviceSerial':item.get('deviceSerial'),
                'netAddress':item.get('netAddress'),
                'addTime':item.get('addTime'),
                'updateTime':item.get('updateTime'),
                '状态': '在线' if str(item.get('status')) == '1' else '离线',
                'live_url':self.get_live(item.get('deviceSerial')),
            }
            print(data)            
            save_result('ys_res.txt',data)
    # post
    def post(self,api_url,data):
        base_url='https://open.ys7.com'
        results = requests.post(base_url + api_url, data,  verify=False)
        # print(results.json())
        if(str(results.json().get('code')) == '200'):
            return results.json()
        else:
            print('request_error:' + results.json().get('msg')  +"\n raw:" + api_url + '\n' + str(results.request.body))
            exit()

def save_result(filename,data):
    with open(filename,'a+') as f:
        f.write(str(data))
        f.write("\n")
        print('已保存结果至'+filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Your script description here')
    parser.add_argument('-m', type=str, help='选择利用的模块(hik,ys)')
    parser.add_argument('-appkey', type=str, help='AppKey')
    parser.add_argument('-secret', type=str, help='Secret')
    parser.add_argument('-u', type=str, help='hik模块必选 (e.g., http://1.1.1.1:1443)')
    args = parser.parse_args()

    if args.m:
        if args.m == 'hik':
            hik = Hik(args.u,args.appkey,args.secret)
            hik.exp()
        elif args.m == 'ys':
            ys = Ys(args.appkey,args.secret)
            ys.exp()
        