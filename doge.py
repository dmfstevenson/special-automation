import json
import requests

credentials = 'Your Credential API HTTPS Req here.... keep secret'
response = requests.get("https://www.coinspot.com.au/pubapi/latest")

doge_price=response.json()
message = ('$DOGEcoin is at %s AUD, Not long until we hit the moon, Justin!' % doge_price['prices']['doge']['ask'])
 

def post_to_slack(message,credentials):
    data = {'text':message}
    url = (credentials)
    requests.post(url,json=data, verify=True)
 
 
if __name__ == '__main__':
    post_to_slack(message,credentials)
