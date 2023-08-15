# coding:utf-8
import time
import sys
import commands
import m3u8
import requests
import os
import traceback
from bs4 import BeautifulSoup
from Crypto.Cipher import AES

USER_AGENT = {'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_3 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13E188a Safari/601.1', 'Referer': 'http://www.houdoukyoku.jp/sp/', 'X-Playback-Session-Id': 'B741C93A-CA7B-41E5-B6D1-7EC2A6739EF8'}
target_url = 'http://www.houdoukyoku.jp/sp/'
rokuzikan = sys.argv[1]
zitime = 60 / 10 * int(rokuzikan)
CH_PATH = "/var/www/homeserver/pg/nya/nya_in/"
OUT_PATH = "/var/www/homeserver/pg/nya/nya_out/"
ffmpeg_join_name = time.strftime('%Y-%m-%d-%H-%M')
request_out = 0

#driver = webdriver.PhantomJS()
r1 = requests.get(target_url, headers=USER_AGENT)
r1_body = r1.text

soup = BeautifulSoup(r1_body, "lxml")
meta_url = soup.find('video').get("src")
m3u8_meta = m3u8.load(meta_url)
#list
llist = []
ts_list_end = []

for paw in m3u8_meta.playlists:
  llist.append(paw.uri)

m3u8_ts = m3u8.load(llist[0])

sequn = m3u8_ts.media_sequence
endtime = zitime + sequn
#print isinstance(sequn, int)
#print isinstance(endtime, int)

#key_file
key_url = requests.get(m3u8_ts.key.uri)
key_file = ''.join(['%02x' %ord(s) for s in key_url.content]).decode('hex')
iv_file_64 = m3u8_ts.key.iv[2:34]
iv_file = iv_file_64.decode('hex')

while True:
  if sequn >= endtime:
    break
  rr = requests.get("http://hodokyoku-jp-live1.hls1.fmslive.stream.ne.jp/hls-live/streams/hodokyoku-jp-live1/events/_definst_/phlslive/hodokyoku-jp-lowNum"+str(sequn)+".ts", headers=USER_AGENT)
  if rr.status_code == 200:
    #print "status 200 sequn:%s" % sequn
    try:
      ts_name = 'hodokyoku-jp-lowNum'+str(sequn)+'.ts'
      ts_file=open(CH_PATH+ts_name,'w')
      aes = AES.new(key_file, AES.MODE_CBC, iv_file)
      decrypt_data = aes.decrypt(rr.content)
      ts_file.write(decrypt_data)
      ts_list_end.append(ts_name)
      #ts_file.write(rr.content)
    except:
      print "error saving", sequn
      print(traceback.format_exc())
    finally:
      ts_file.close()
      time.sleep(10)
      request_out = 0
      sequn += 1

  else:
    request_out += 1
    print request_out
    if request_out >= 10:
      break
    else:
      print "not while"

ts_list = ''
for ts_list_str in ts_list_end:
  ts_list += CH_PATH+ts_list_str+'|'


#ts_list = '|'.join(ts_list_end).CH_PATH
ffmpeg_join = commands.getoutput('ffmpeg -i \"concat:'+ts_list+'\" -c copy '+OUT_PATH+'houdoukyoku'+ffmpeg_join_name+'.ts')

#file delete
for ts_list_d in ts_list_end:
  os.remove(CH_PATH+ts_list_d)
else:
  print "not removed"

