import requests
from bs4 import BeautifulSoup

def do_search(q):
    req = requests.get('https://youtube.com/results', params={'search_query': q})
    soup = BeautifulSoup(req.text, 'html.parser')
    links = soup.find_all('a', {'class': 'yt-uix-tile-link'})
    titles = map(lambda l: l.text, links)
    ids = map(lambda l: (lambda h: h[h.find('watch?v=')+8:])(l['href']), links)
    return list(zip(titles, ids))
