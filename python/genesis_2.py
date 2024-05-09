import os
import requests
import pandas as pd
import json
from rich import print as rprint
import io  # Correctly import io for StringIO

# Load sensitive data from environment variables for security
USER_ID = 'DE17T29R57'
PASSWORD = '4Bf/3Ap)3]r2,,h'
GENESIS_URL = 'https://www-genesis.destatis.de/genesisWS/rest/2020/data/cube?'

# Function to build the API URL
def build_url(tab_code, area_type, content, start_year, classifier1, classifier2, key1, key2, lang):
    return (
        f"{GENESIS_URL}username={USER_ID}&password={PASSWORD}&name={tab_code}&area={area_type}"
        f"&compress=true&contents={content}&startyear={start_year}&classifyingvariable1={classifier1}"
        f"&classifyingkey1={key1}&classifyingvariable2={classifier2}&classifyingkey2={key2}&language={lang}"
    )

# Function to fetch and parse data
def fetch_and_parse_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)["Object"]['Content'].split('\n')
        header = 'field_D;classifyingkey1;field_DFDN;quarter;year;value;field_e;field_;field__'
        return pd.read_csv(io.StringIO(header + '\n' + '\n'.join(data[14:])), delimiter=';')
    else:
        raise Exception("Failed to fetch data from API")

# Function to transform data into a structured JSON format
def transform_data(df, tab_code, content, classifier1, key1, classifier2, key2):
    result = {'tab_code': tab_code, 'content': content, 'classifier1': classifier1, 'key1': key1,
              'classifier2': classifier2, 'key2': key2, 'data': []}
    for year, group in df.groupby('year'):
        year_data = {'year': year, 'df': [{'quarter': row['quarter'], 'value': row['value']} for _, row in group.iterrows()]}
        result['data'].append(year_data)
    return result

# Main function to execute the script
def main():
    tab_code = '61241BM010'
    area_type = 'all'
    content = 'VST066'
    start_year = ''
    classifier1 = 'BEORT1'
    classifier2 = 'LFGAT1'
    key1 = '11000000'
    key2 = 'LIEFERUNGOEL02'
    lang = 'en'

    url = build_url(tab_code, area_type, content, start_year, classifier1, classifier2, key1, key2, lang)
    df = fetch_and_parse_data(url)
    transformed_data = transform_data(df, tab_code, content, classifier1, key1, classifier2, key2)  # Pass all variables as arguments
    rprint(json.dumps(transformed_data, indent=4))

if __name__ == '__main__':
    main()
