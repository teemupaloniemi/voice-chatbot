from googlesearch import search
import requests
from bs4 import BeautifulSoup
import re

def get_text_content(query):
    for url in search(query, tld="co.in", num=2, stop=2, pause=2):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = ' '.join([element.get_text() for element in soup.find_all(['p'])])
                text_content = re.sub(r'\s+', ' ', text_content)
                return text_content    
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
    
