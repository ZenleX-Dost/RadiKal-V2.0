"""Test thumbnail in history response."""
import requests

r = requests.get('http://localhost:8000/api/xai-qc/history?page=1&page_size=1')
d = r.json()
a = d['analyses'][0] if d['analyses'] else {}
print('Has thumbnail:', 'thumbnail' in a)
print('Thumbnail value:', a.get('thumbnail')[:50] if a.get('thumbnail') else 'None')
print('Thumbnail length:', len(a.get('thumbnail', '') or '') if a.get('thumbnail') else 0)
