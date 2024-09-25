import pandas as pd
import requests
import dart_fss as dart
import json

#다트에서 리스트 가져오기

api_key ="aca7c9a43352f3d2bd46ff80a28e2a697e9ed858"

dart.set_api_key(api_key=api_key)

all = dart.api.filings.get_corp_code()
df_all = pd.DataFrame(all)
df_listed = df_all[df_all['stock_code'].notnull()]

df_all.to_csv('all_corp.csv', encoding='utf-8', index=False)
df_listed.to_csv('listed_corp.csv', encoding='utf-8', index=False)