from urllib.request import urlopen

url = 'http://127.0.0.1:8000/propostas/4'
try:
    r = urlopen(url).read().decode('utf-8')
    found = 'name="caixas[' in r
    print('has caixas inputs:', found)
    idx = r.find('Simulação por Volumes')
    if idx != -1:
        print(r[idx:idx+800])
    else:
        print('Simulação por Volumes section not found')
except Exception as e:
    print('error fetching:', e)
