import config
import requests
import utils


def get_temp_press():
    url = f'{config.server_url}/api/receiveLogs'
    response = requests.get(url)
    print(response)
    logs = response.json()
    beds_logs = [{'id': i+1, 'values': None} for i in range(config.beds_number)]
    for i in range(config.beds_number):
        bed_logs = [item for item in logs if (item.get('topic') and item.get('topic').get('id') == i+1)]
        if bed_logs:
            beds_logs[i]['values'] = bed_logs[0].get('message')
    return beds_logs

def get_devices_status():
    fan_statuses = {0: 'Выключен', 1: 'Включён'}
    windows_statuses = {0: 'Закрыты', 1: 'Открыты наполовину', 2: 'Открыты полностью'}
    url = f'{config.server_url}/api/sendLogs'
    response = requests.get(url)
    logs = response.json()
    fan, windows = None, None
    for row in logs:
        if row.get('topic').get('name') == 'order/fan':
            fan = fan_statuses.get(row.get('command'))
            break
    for row in logs:
        if row.get('topic').get('name') == 'order/windows':
            windows = windows_statuses.get(row.get('command'))
    return {'fan': fan, 'windows': windows}


def get_humidity():
    url = f'{config.server_url}/api/humidity'
    response = requests.get(url)
    logs = response.json()
    beds_logs = [{'id': i+1, 'value': None} for i in range(config.beds_number)]
    for i in range(config.beds_number):
        bed_logs = [item for item in logs if item.get('bed') == i+1]
        if bed_logs:
            beds_logs[i]['value'] = bed_logs[0]['value']
    return beds_logs


def get_measures():
    url_tp = f'{config.server_url}/api/receiveLogs'
    url_h = f'{config.server_url}/api/humidity'
    response_tp = requests.get(url_tp)
    response_h = requests.get(url_h)
    logs_tp = response_tp.json()
    logs_h = response_h.json()
    beds_measures = [{'id': i+1, 'measures': {'temperature': None, 'pressure': None, 'humidity': None}} for i in range(config.beds_number)]
    for i in range(config.beds_number):
        bed_logs_tp = [item for item in logs_tp if (item.get('topic') and item.get('topic').get('id') == i+1)]
        tp_measures = [[item.get('message'), item.get('time')] for item in bed_logs_tp]
        bed_logs_h = [item for item in logs_h if item.get('bed') == i+1]
        h_measures = [[item.get('value'), item.get('time')] for item in bed_logs_h]
        beds_measures[i]['measures']['temperature'] = [[item[0].get('temperature'), utils.transform_time(item[1])] for item in tp_measures[:5]]
        beds_measures[i]['measures']['pressure'] = [[item[0].get('pressure'), utils.transform_time(item[1])] for item in tp_measures[:5]]
        beds_measures[i]['measures']['humidity'] = [[item[0], utils.transform_time(item[1])] for item in h_measures[:5]]
    return beds_measures
def get_configurations():
    url = f'{config.server_url}/api/configurations'
    response = requests.get(url)
    return response.json()


def get_configuration_by_id(config_id: int):
    configurations = get_configurations()
    for config in configurations:
        if config['id'] == config_id:
            return config


def create_configuration(configuration: dict):
    url = f'{config.server_url}/api/configurations'
    response = requests.post(url, json=configuration)


def change_configuration(configuration: dict):
    url = f'''{config.server_url}/api/configurations/{configuration.get('id')}'''
    response = requests.put(url, json=configuration)


def disable_configuration(config_id: int):
    config = get_configuration_by_id(config_id)
    config['active'] = False
    change_configuration(config)
def enable_configuration(config_id: int):
    config = get_configuration_by_id(config_id)
    bed = config.get('bed')
    configs = get_configurations()
    for c in configs:
        if c.get('bed') == bed:
            disable_configuration(c.get('id'))
    config['active'] = True
    change_configuration(config)