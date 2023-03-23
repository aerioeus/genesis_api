import json
import requests
import csv
import io

genesis_url = 'https://www-genesis.destatis.de/genesisWS/rest/2020/data/cube?'
user_id = 'DE17T29R57'
password = '4Bf/3Ap)3]r2,,h'
tab_code = '62221BV002'
area_type = 'all'
content = 'VST066'
start_year = ''  # '2018'
classifiyer1 = 'WZ08C7'
classifyingkey1 = 'WZ08-D-06'
lang = 'en'

# Open genesis API URL
destatis = f"{genesis_url}username={user_id}&password={password}&name={tab_code}&area={area_type}&compress=true&contents={content}&startyear={start_year}&classifyingvariable1={classifiyer1}&classifyingkey1={classifyingkey1}&language={lang}"

# get data from GENESIS API, converts it to JSON, get the CSV content and splits the lines
responseContent = json.loads(requests.get(destatis).text)["Object"]['Content'].split('\n')

# add a new line with the field names to the CSV content, eliminating unecessary lines
parsedContent = ['field_D;classifyingkey1;field_DFDN;quarter;year;value;field_e;field_;field__'] + responseContent[14:]

# convert parsed content to CSV in order to transform data into readable objects that can be manipulated
csvReader = csv.DictReader(io.StringIO('\n'.join(parsedContent)), delimiter=';', lineterminator='\n')
jsonArray = []
for row in csvReader:
    jsonArray.append(row)

# initialize the result object
result = {
    'tab_code': tab_code,
    'content': content,
    'classifiyer1': classifiyer1,
    'classifyingkey1': classifyingkey1,
    'data': []
}

# loop through a list of years in order to form a JSON object easy to read
years = list(dict.fromkeys([obj['year'] for obj in jsonArray]))
for year in years:
    yearData = {'year': year}
    df = []
    dn = []
    # loop through CSV lines separated by year
    for obj in [obj for obj in jsonArray if obj['year'] == year]:
        quarterValue = {'quarter': obj['quarter'], 'value': obj['value']}
        # split result in 'DF' or 'DN' (need to understand what it means, as there are quartes for this DF and for DN)
        df.append(quarterValue) if obj['field_DFDN'] == 'DF' else dn.append(quarterValue)

    yearData.update({'df': df, 'dn': dn})
    result['data'].append(yearData)

print(json.dumps(result))
