import requests


def wow_player_count():
    url = 'http://192.168.1.7:3000/data'
    try:
        response = requests.get(url)
        response.raise_for_status()
    
        data = response.json()
        count = data[0].get('COUNT(*)', 'Key not found')
        return str(count)
    
    
    except requests.RequestException as e:
        return str(99)
