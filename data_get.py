import requests
import urllib.parse as urlparse
from urllib.parse import urlencode
import pandas as pd
import json
import os

SPEED_INFO = "http://opendata.sz.gov.cn/api/29200_00403590/1/service.xhtml?"
APP_KEY = "c16df26c7c3f43dabad36aa74da92b4a"
#For inumeration
PAGES=8000

def main():
    df = get_range(PAGES,SPEED_INFO)
    split_Data(df)


def split_Data(full_table):
    times=full_table.TIME.unique().tolist()
    periods=full_table.PERIOD.unique().tolist()
    for time in times:
        date_temp = full_table[full_table['TIME'] == time]
        for period in periods:
            period_temp = date_temp[date_temp['PERIOD'] == period]
            store_Data(period_temp,join_path(time),period)


def join_path(time):
    return os.path.join("data/speed",time)

def store_Data(df,dir,period):
    if not os.path.exists(dir):
        os.mkdir(dir)
    df.to_csv(os.path.join(dir,str(period)+".csv"), index=False)


#parse url with parameters to return a single url
def parse_URL(params, url):
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qs(url_parts[4]))
    query.update(params)
    url_parts[4] = urlencode(query)
    urlget = urlparse.urlunparse(url_parts)
    print(urlget)
    return urlget

#return a get request text in json
def get_URL(page,url):
    params = {'page':page,'row':1,'appKey':APP_KEY}
    try:
        r = requests.get(url = parse_URL(params,url))
    except:
        print("error")
    return json.loads(r.text)['data']

#input the desired range to pull data from, and return in a dataframe
def get_range(page,url):
    all_res = []
    for page in range(7000,PAGES+1):
        dfTemp = pd.DataFrame(get_URL(page,url))
        all_res.append(dfTemp)
    df_res = pd.concat(all_res)
    return df_res



if __name__ == "__main__":
    main()
