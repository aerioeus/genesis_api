import boto3
import json
import requests
import csv
import io
import re
from decimal import Decimal

def getIndexContent(cubeCode: str, classifyingVar1: str = None, classifyingKey1: str = None, classifyingVar2: str = None, classifyingKey2: str = None,
                    classifyingVar3: str = None, classifyingKey3: str = None) -> list[str]:
    genesis_url = 'https://www-genesis.destatis.de/genesisWS/rest/2020/data/cube?'
    user_id = 'DE17T29R57'
    password = '4Bf/3Ap)3]r2,,h'

    destatis = f'{genesis_url}username={user_id}&password={password}&language=en&name={cubeCode}&classifyingvariable1={classifyingVar1}&classifyingkey1={classifyingKey1}'
    if classifyingVar1 != None:
        destatis += f'&classifyingvariable1={classifyingVar1}'
    if classifyingKey1 != None:
        destatis += f'&classifyingkey1={classifyingKey1}'

    if classifyingVar2 != None:
        destatis += f'&classifyingvariable2={classifyingVar2}'
    if classifyingKey2 != None:
        destatis += f'&classifyingkey2={classifyingKey2}'

    if classifyingVar3 != None:
        destatis += f'&classifyingvariable3={classifyingVar3}'
    if classifyingKey3 != None:
        destatis += f'&classifyingkey3={classifyingKey3}'

    # get data from GENESIS API, converts it to JSON, get the CSV content and splits the lines
    jsonLoad = json.loads(requests.get(destatis).text)
    content = jsonLoad["Object"]['Content']
    return content.split('\n')

def processIndexContent(content: list[str], baseYearPosition: int, contentStartPos: int, indexName: str, cubeCode: str, classifyingVar1: str = None,
                        classifyingKey1: str = None, classifyingVar2: str = None, classifyingKey2: str = None, classifyingVar3: str = None,
                        classifyingKey3: str = None, hasDplusField = True) -> None:

    csvHeader = 'field_D;'
    #get base year info
    #'D;VST066;2020=100;FEST;PROZENT;1;;N'
    baseYear = re.search(r'\d{4}=\d{3}', content[baseYearPosition])
    baseYear = baseYear.group() if baseYear else 'N/A'

    # initialize the result object
    # table keys:
    # pk -> item_type
    # sk -> id
    # lsi_1 -> lsi_1
    dbItemId = f'IDX#{cubeCode}'
    dbItem = {
        'item_type': 'index',
        'index_name': indexName,
        'cube_id': cubeCode,
        'base_year_info': baseYear,
    }
    if classifyingVar1 != None:
        dbItem.update({'classifyingvariable1': classifyingVar1})
        dbItemId += f'#{classifyingVar1}'
    if classifyingKey1 != None:
        dbItem.update({'classifyingkey1': classifyingKey1})
        dbItemId += f'#{classifyingKey1}'
        csvHeader += 'classifyingkey1;'

    if classifyingVar2 != None:
        dbItem.update({'classifyingvariable2': classifyingVar2})
        dbItemId += f'#{classifyingVar2}'
    if classifyingKey2 != None:
        dbItem.update({'classifyingkey2': classifyingKey2})
        dbItemId += f'#{classifyingKey2}'
        csvHeader += 'classifyingkey2;'

    if classifyingVar3 != None:
        dbItem.update({'classifyingvariable3': classifyingVar3})
        dbItemId += f'#{classifyingVar3}'
    if classifyingKey3 != None:
        dbItem.update({'classifyingkey3': classifyingKey3})
        dbItemId += f'#{classifyingKey3}'
        csvHeader += 'classifyingkey3;'

    # add a new line with the field names to the CSV content, eliminating unecessary lines
    #D;GP09-353;DG;MONAT01;1976;32.0;e;;0.0
    parsedContent = [csvHeader + f"{'field_DPlus;' if hasDplusField else ''}" + 'period;year;value;field_e;field_;field__'] + content[contentStartPos:]

    # convert parsed content to CSV in order to transform data into readable objects that can be manipulated
    csvReader = csv.DictReader(io.StringIO('\n'.join(parsedContent)), delimiter=';', lineterminator='\n')
    jsonArray = []
    for row in csvReader:
        jsonArray.append(row)

    # loop through a list of years in order to form a JSON object easy to read
    years = list(dict.fromkeys([obj['year'] for obj in jsonArray]))
    with table.batch_writer() as batch:
        for year in years:
            # loop through CSV lines separated by year
            for obj in [obj for obj in jsonArray if obj['year'] == year]:
                period = obj['period']
                result = {
                    'id': dbItemId + f'#{year}#{period}',
                    'lsi_1': f'{indexName}#{year}#{period}',
                    'year': int(year),
                    'period': period,
                    'value': Decimal(obj['value'])
                }
                result.update(dbItem)
                batch.put_item(result)

    print(f'Finished with {dbItemId}')


def lambda_handler(event, context):
    tab_code = '61241BM003'
    classifyingvariable1 = 'GP09M3'
    classifyingkey1 = 'GP09-353'
    responseContent = getIndexContent(tab_code, classifyingvariable1, classifyingkey1)
    processIndexContent(responseContent, 12, 14, 'Fernwärmeindex', tab_code, classifyingvariable1, classifyingkey1)

    tab_code = '61241BM008'
    classifyingvariable1 = 'GP09N2'
    classifyingkey1 = 'GP-X002'
    responseContent = getIndexContent(tab_code, classifyingvariable1, classifyingkey1)
    processIndexContent(responseContent, 12, 14, 'Erzeugnisse der Investitionsgüterproduzenten', tab_code, classifyingvariable1, classifyingkey1)


    tab_code = '61241BM006'
    classifyingvariable1 = 'GP09M6'
    classifyingkey1 = 'GP09-351113'
    responseContent = getIndexContent(tab_code, classifyingvariable1, classifyingkey1)
    processIndexContent(responseContent, 12, 14, 'Elektr. Strom, bei Abgabe an gewerbliche Anlagen', tab_code, classifyingvariable1, classifyingkey1)


    tab_code = '61241BM007'
    classifyingvariable1 = 'GP09N1'
    classifyingkey1 = 'GP09-1920260053'
    responseContent = getIndexContent(tab_code, classifyingvariable1, classifyingkey1)
    processIndexContent(responseContent, 12, 14, 'Dieselkraftstoff ab Tankstelle', tab_code, classifyingvariable1, classifyingkey1)

    tab_code = '61241BM003'
    classifyingvariable1 = 'GP09M3'
    classifyingkey1 = 'GP09-253'
    responseContent = getIndexContent(tab_code, classifyingvariable1, classifyingkey1)
    processIndexContent(responseContent, 12, 14, 'Dampfkessel (Dampferzeuger) (ohne Zentralheizungs- kessel); Kernreaktoren, Teile dafür', tab_code, classifyingvariable1, classifyingkey1)

    tab_code = '61111BM001'
    responseContent = getIndexContent(tab_code)
    processIndexContent(responseContent, 11, 13, 'Verbraucherpreisindex für Deutschland; Verbraucherpreis insgesamt', tab_code)

    # #need content
    # tab_code = '62221BV001'
    # classifyingvariable1 = 'WZ08C7'
    # classifyingkey1 = 'WZ08-D-06'
    # responseContent = getIndexContent(tab_code, classifyingvariable1, classifyingkey1)
    # processIndexContent(responseContent, 12, 14, 'Index der tariflichen Monatsverdienste ohne Sonderzahlungen nach Quartalen und ausgewählten Wirtschaftszweigen für Energie- u. Wasserversorgung', tab_code, classifyingvariable1, classifyingkey1)

    # #need content
    # tab_code = '62221BV001'
    # classifyingvariable1 = 'WZ08C7'
    # classifyingkey1 = 'WZ08-D'
    # responseContent = getIndexContent(tab_code, classifyingvariable1, classifyingkey1)
    # processIndexContent(responseContent, 12, 14, 'Index der tariflichen Monatsverdienste ohne Sonderzahlungen nach Quartalen und ausgewählten Wirtschaftszweigen für Energieversorgung', tab_code, classifyingvariable1, classifyingkey1)

    tab_code = '61261BV002'
    classifyingvariable1 = 'STEMW1'
    classifyingkey1 = 'STEMW1'
    classifyingvariable2 = 'BAUIN2'
    classifyingkey2 = 'BPI4'
    classifyingvariable3 = 'BAUIN1'
    classifyingkey3 = 'BPNB525'
    responseContent = getIndexContent(tab_code, classifyingvariable1, classifyingkey1, classifyingvariable2, classifyingkey2, classifyingvariable3, classifyingkey3)
    processIndexContent(responseContent, 14, 16, 'Instandhaltung von Wohngebäuden - Heizanlagen u. zentrale Wassererwärmungsanl', tab_code, classifyingvariable1, classifyingkey1, classifyingvariable2, classifyingkey2, classifyingvariable3, classifyingkey3)

    tab_code = '61241BM010'
    classifyingvariable1 = 'BEORT1'
    classifyingkey1 = 'RHEINSCHIENE'
    classifyingvariable2 = 'LFGAT1'
    classifyingkey2 = 'LIEFERUNGOEL02'
    responseContent = getIndexContent(tab_code, classifyingvariable1, classifyingkey1, classifyingvariable2, classifyingkey2)
    processIndexContent(responseContent, 12, 14, 'Preise für Leichtes Heizöl nach ausgewählten Marktorten bei Lieferung in Tankkraftwagen an Verbraucher, 40 - 50 hl pro Auftrag, frei Verbraucher. RHEINSCHIENE', tab_code, classifyingvariable1, classifyingkey1, classifyingvariable2, classifyingkey2, hasDplusField=False)

    tab_code = '61241BM010'
    classifyingvariable1 = 'BEORT1'
    classifyingkey1 = '11000000'
    classifyingvariable2 = 'LFGAT1'
    classifyingkey2 = 'LIEFERUNGOEL02'
    responseContent = getIndexContent(tab_code, classifyingvariable1, classifyingkey1, classifyingvariable2, classifyingkey2)
    processIndexContent(responseContent, 12, 14, 'Preise für Leichtes Heizöl nach ausgewählten Marktorten bei Lieferung in Tankkraftwagen an Verbraucher, 40 - 50 hl pro Auftrag, frei Verbraucher. BERLIN', tab_code, classifyingvariable1, classifyingkey1, classifyingvariable2, classifyingkey2, hasDplusField=False)

table = boto3.resource('dynamodb').Table("NewASA")
lambda_handler({},{})