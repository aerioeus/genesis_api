import json
import requests
from decimal import Decimal
import re
import pandas as pd
import boto3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='app.log', filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

def build_url(config):
    """Builds the request URL from configuration."""
    url = (f"{config['genesis_url']}username={config['user_id']}&password={config['password']}&language=de"
           f"&name={config['cubecode']}&area={config['areatype']}&compress=true")
    if config['classifier1']:
        url += f'&classifyingvariable1={config['classifier1']}'
    if config['key1']:
        url += f'&classifyingkey1={config['key1']}'
    if config['classifier2']:
        url += f'&classifyingvariable2={config['classifier2']}'
    if config['key2']:
        url += f'&classifyingkey2={config['key2']}'
    return url

def make_request(url):
    """Makes a HTTP GET request and handles potential errors."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises a HTTPError for bad responses
        return response
    except requests.RequestException as e:
        logging.error(f"HTTP request error: {e}")
        raise SystemExit(e)

def parse_data(response_text):
    """Parses JSON data from the HTTP response."""
    try:
        parsed_json = json.loads(response_text, parse_float=Decimal)
        return parsed_json
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        raise

def extract_data(parsed_json):
    """Extracts data from JSON and processes it into a DataFrame."""
    try:
        data = parsed_json["Object"]['Content'].split('\n')
        info_pattern = re.compile(r'\d+=100')
        info_matches = [match for line in data for match in info_pattern.findall(line)]
        info_matches_str = ', '.join(info_matches)
        filtered_response = [line + " " + info_matches_str for line in data if 'D' in line and 'e' in line and ('MONAT' in line or 'QUART' in line)]
        extracted_data = [{'field_D': parts[0], 'classifyingkey1': parts[1], 'classifyingkey2': parts[2],
                           'period': parts[3], 'year': int(parts[4]), 'value': float(parts[5]), 'field_e': parts[6],
                           'base': info_matches_str}
                          for parts in (line.split(';') for line in filtered_response)]
        return pd.DataFrame(extracted_data)
    except Exception as e:
        logging.error(f"Data extraction error: {e}")
        raise

def prepare_data_for_dynamodb(df, period_key):
    """Prepares data for uploading to DynamoDB."""
    try:
        result = {'data': []}
        for year, group in df.groupby('year'):
            result['data'].append({
                'year': year,
                'df': [{'period': row[period_key], 'value': row['value'], 'base': row['base']}
                       for _, row in group.iterrows()]
            })
        return result
    except Exception as e:
        logging.error(f"Error preparing data for DynamoDB: {e}")
        raise

def upload_to_dynamodb(table, data_dict):
    """Uploads prepared data to DynamoDB with detailed error handling."""
    try:
        for year_info in data_dict['data']:
            for month_data in year_info['df']:
                sort_key = f"IND#{data_dict['cubeCode']}#{year_info['year']}#{month_data['period']}"
                item = {
                    'pk': 'index', 'sk': sort_key,
                    'lsi1': data_dict['cubeCode'],
                    'attribute1': data_dict['classifyingVar1'],
                    'attribute2': data_dict['classifyingKey1'],
                    'attribute3': year_info['year'],
                    'attribute4': month_data['period'],
                    'attribute5': Decimal(str(month_data['value'])),
                    'attribute6': month_data['base']
                }
                table.put_item(Item=item)
                logging.info(f"Uploaded item: {item}")
    except Exception as e:
        logging.error(f"Error uploading to DynamoDB: {e}")
        raise

# Configuration
config = {
    'genesis_url': 'https://www-genesis.destatis.de/genesisWS/rest/2020/data/cube?',
    'user_id': 'DE17T29R57',
    'password': '4Bf/3Ap)3]r2,,h',
    'cubecode': '61241BM010',
    'areatype': 'all',
    'classifier1': 'BEORT1',
    'classifier2': 'LFGAT1',
    'key1': '11000000',
    'key2': 'LIEFERUNGOEL02',
    'lang': 'en'
}

if __name__ == '__main__':
    url = build_url(config)
    response = make_request(url)
    parsed_json = parse_data(response.text)
    df = extract_data(parsed_json)
    period_key = 'quarter' if df['period'].str.contains('Q').any() else 'month'
    result = prepare_data_for_dynamodb(df, period_key)
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('onetable')
    upload_to_dynamodb(table, result)
