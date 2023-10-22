import requests
import json

class McServer:
    def __init__(self):
        self.api = "https://api.mcstatus.io/v2/status/java/172.103.142.196:25565"

    def get_status(self):
        response = requests.get(self.api)
        if response.status_code != 200:
            return "minecraft"
        response = json.loads(response.content)
        return_str = ''
        if response['online']:
            return_str += '🌳'
            if 'players' in response:
                players = response['players']['online']
                if players > 0:
                    return_str += '_' + str(players) + '_'
        else:
            return_str += '🛑'

        return_str += 'minecraft'
        return return_str
