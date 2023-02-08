import pandas as pd
from bs4 import BeautifulSoup
#import mechanize
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

with open('Pair_Trains.txt') as g:
  pairsdata = g.read()
pairsdict = json.loads(pairsdata)
#print(pairsdict)

trainslist=open('trainnos.txt','r')
Ultimatestart_time = time.time()

driver = webdriver.Chrome(options=chrome_options)
#driver.maximize_window()
driver.get('https://www.irctc.co.in/nget/booking/check-train-schedule')

#disable chatbot
#wait(driver,15).until(EC.visibility_of_element_located((By.XPATH,'//*[@id="disha-banner-close"]'))).click()

#go to train schedule section
driver.find_element(By.XPATH,'/html/body/app-root/app-home/div[1]/app-header/div[1]/div[2]').click()
driver.find_element(By.XPATH,'//*[@id="slide-menu"]/p-sidebar/div/nav/ul/li[3]/label/span[2]').click()
driver.find_element(By.XPATH,'//*[@id="slide-menu"]/p-sidebar/div/nav/ul/li[3]/ul/li[7]/a/span').click()


#Start extracting train info
for no in range(5):
  if no<0:
    number=trainslist.readline()
    continue
  start_time = time.time()
  number=trainslist.readline()
  number=number.strip()
  print(number)
  wait(driver,15).until(EC.visibility_of_element_located((By.XPATH,'//*[@id="train"]/span/input')))
  num=driver.find_element(By.XPATH,'//*[@id="train"]/span/input')
  num.send_keys(number)
  time.sleep(3)
  
  try:
    dropdownsel=driver.find_element(By.XPATH,'//*[@id="pr_id_3_list"]/li')
    sug=dropdownsel.text
    if sug=='No Train Found':
      with open('invalidnos.csv','a') as f:
            f.writelines([number,'\n'])
            num.clear()
      continue
    dropdownsel.click() 
    time.sleep(8)
   #check=wait(driver,15).until(EC.presence_of_element_located((By.XPATH,'//*[@id="divMain"]/div/app-check-train-schedule/div[2]/div/div/div/div[3]'))).text
   #print(check,'checked')
  
    check=wait(driver,15).until(EC.presence_of_element_located((By.XPATH,'//*[@id="divMain"]/div/app-check-train-schedule/div[2]/div/div/div/div[3]'))).text
    #print(check)
    if check=='Train does not run at given date':
        with open('recheck.csv','a') as f:
            f.writelines([number,'\n'])
            num.clear()
        continue
    elif check=='Invalid Train Number.':
        with open('invalidnos.csv','a') as g:
            g.writelines([number,'\n'])
            num.clear()
        continue
    elif check=='':
        with open('validnos.csv','a') as g:
            g.writelines([number,'\n'])
  except:
    num.clear()
    with open('errornos.csv','a') as g:
        g.writelines([number,'\n'])
    continue
  #time.sleep(2)
  ltime=time.time()
  Break=0
  while(1):
    tnumber=wait(driver,15).until(EC.presence_of_element_located((By.XPATH,'//*[@id="divMain"]/div/app-check-train-schedule/div[2]/div/div[2]/div[1]/div[2]/div[1]'))).text
    if  tnumber==number:
      break
    else:
      time.sleep(2)
      if  (time.time() - ltime)>30:
        with open('mismatch.csv','a') as g:
          g.writelines([number,'\n'])
          num.clear()
        Break=1
        break

  if Break==1:
    continue
   
  
  trainname=driver.find_element(By.XPATH,'//*[@id="divMain"]/div/app-check-train-schedule/div[2]/div/div[2]/div[1]/div[2]/div[2]').text
  fromstation=driver.find_element(By.XPATH,'//*[@id="divMain"]/div/app-check-train-schedule/div[2]/div/div[2]/div[1]/div[2]/div[3]').text
  tostation=driver.find_element(By.XPATH,'//*[@id="divMain"]/div/app-check-train-schedule/div[2]/div/div[2]/div[1]/div[2]/div[4]').text
  
  #check and generate list of days on which train run
  daylist=[]
  for i in range(1,8):
    daycolor=driver.find_element(By.XPATH,'//*[@id="divMain"]/div/app-check-train-schedule/div[2]/div/div[2]/div[1]/div[2]/div[5]/div['+str(i)+']').value_of_css_property('background-color')
    if daycolor=='rgba(195, 255, 195, 1)':
      daylist.append(1)
    else:
      daylist.append(0)
    #daycolorlist.append(daycolor)
   
  soup = BeautifulSoup(driver.page_source, 'lxml')
  tables = soup.find_all('table')
  dfs = pd.read_html(str(tables),flavor='bs4')
  try:
    dict=dfs[0].set_index('Station Code').to_dict('index')
    durdict=dfs[0].to_dict('index')
  except ValueError:
    with open('exception double routes.csv','a') as f:
        f.writelines([number,'\n'])
    num.clear()
    continue
  
  #print(dict)
  if len(durdict)==0:
    num.clear()
    continue
  days=durdict[len(durdict)-1]['Day']
  Distance=durdict[len(durdict)-1]['Distance']
  starttime=durdict[0]['Departure Time'].split(":")
  starttime=int(starttime[0])*60+int(starttime[1])
  endtime=durdict[len(durdict)-1]['Arrival Time'].split(":")
  #print(endtime)
  endtime=int(endtime[0])*60+int(endtime[1])
  #print(endtime)
  duration=(days-1)*1440-starttime+endtime
  min=duration%60
  hour=duration//60
  if min<10:
    Duration=str(hour)+':0'+str(min)
  else:
    Duration=str(hour)+':'+str(min)
  #print(Duration,days,starttime,endtime )

  trains_dictionary={number:{'Train_name':trainname,'From_station':fromstation,'To_station':tostation,'Pair':pairsdict[number],'Duration':Duration,'Distance':Distance,'Runs_on':{'mon': daylist[0],'tue':daylist[1],'wed':daylist[2],'thu':daylist[3],'fri':daylist[4],'sat':daylist[5],'sun':daylist[6]},'Stations':list(dict.keys())}}
  schedules_dictionary={number:dict}
  #print(schedules_dictionary)
  

  with open('trains_dict.json') as f:
    trainsdata = f.read()
  
  with open('schedules_dict.json') as g:
    schedulesdata = g.read()

  if no != 0:
    trainsdict = json.loads(trainsdata)
    schedulesdict=json.loads(schedulesdata)
    if number not in trainsdict.keys():
      trainsdict.update(trains_dictionary)
    if number not in schedulesdict.keys():
      schedulesdict.update(schedules_dictionary)
      

  if no == 0:
    with open('trains_dict.json', 'w') as convert_file:
     convert_file.write(json.dumps(trains_dictionary))
    with open('schedules_dict.json', 'w') as convert_file2:
     convert_file2.write(json.dumps(schedules_dictionary))
     #print('entered')
  else:
    with open('trains_dict.json', 'w') as convert_file:
     convert_file.write(json.dumps(trainsdict))
    with open('schedules_dict.json', 'w') as convert_file2:
     convert_file2.write(json.dumps(schedulesdict))



  

  num.clear()
  print(no+1,"--- %s seconds ---" % (time.time() - start_time))
  
driver.close()
print("--- %s seconds ---" % (time.time() - Ultimatestart_time))

