import requests


def wow_player_count():
    url = 'http://192.168.88.6:3000/data'
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    
        data = response.json()
        count = data[0].get('COUNT(*)', 'Key not found')
        return str(count)
    
    
    except requests.RequestException as e:
        return str("XX")
