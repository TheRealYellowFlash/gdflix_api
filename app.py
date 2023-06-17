from flask import Flask, request, jsonify
from cfscrape import create_scraper
from re import findall, match, search, sub
from urllib.parse import quote, unquote, urlparse
from lxml import etree
from uuid import uuid4
import cloudscraper
from bs4 import BeautifulSoup
import re
app = Flask(__name__)

class DirectDownloadLinkException(Exception):
    """Not method found for extracting direct download link from the http link"""
    pass


def gdflixola(url):
  cget = create_scraper().request
  header = {
        'authority': 'gdflix.lol',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        # 'cookie': 'PHPSESSID=b87583ba8fd5081f4396003bd4f26835',
        'referer': 'https://drive.olamovies.quest/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }
  client = cloudscraper.create_scraper(allow_brotli=False)
  html = client.get(url,headers=header)
  soup = BeautifulSoup(html.text,'lxml')
  if soup.title.text == 'GDFlix | GDFlix':
    return None
  else:
    try:
      title = soup.title.text[9::]
      client = cloudscraper.create_scraper(allow_brotli=False)
      raw = urlparse(url)
      res = client.get(url,headers=header)
      soup = BeautifulSoup(html.text,'lxml')
    except Exception as e:
        raise DirectDownloadLinkException(f'ERROR: {e.__class__.__name__}')
    key = findall('"key",\s+"(.*?)"', res.text)
    if not key:
        raise DirectDownloadLinkException("ERROR: Key not found!")
    key = key[0]
    if not etree.HTML(res.content).xpath("//button[@id='drc']"):
        raise DirectDownloadLinkException("ERROR: This link don't have direct download button")
    boundary = uuid4()
    headers = {
        'Content-Type': f'multipart/form-data; boundary=----WebKitFormBoundary{boundary}',
        'x-token': raw.hostname,
        'useragent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.548.0 Safari/534.10'
    }

    data = f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="action"\r\n\r\ndirect\r\n' \
        f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="key"\r\n\r\n{key}\r\n' \
        f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="action_token"\r\n\r\n\r\n' \
        f'------WebKitFormBoundary{boundary}--\r\n'
    try:
        res = cget("POST", url, cookies=res.cookies, headers=headers, data=data).json()
    except Exception as e:
        raise DirectDownloadLinkException(f'ERROR: {e.__class__.__name__}')
    if "url" not in res:
        raise DirectDownloadLinkException('ERROR: Drive Link not found, Try in your broswer')
    if "drive.google.com" in res["url"]:
        return title,res["url"]
    try:
        res = client.get(res["url"])
    except Exception as e:
        raise DirectDownloadLinkException(f'ERROR: {e.__class__.__name__}')
    drive_links = etree.HTML(res.content).xpath("//a[contains(@class,'btn')]/@href")
    if drive_links and "drive.google.com" in drive_links[0]:
        return title, drive_links[0]
    else:
        return 'FEk'
        
def gdtotv3(url):
  headers = {
      'authority': 'gdtot.pro',
      'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
      'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
      'cache-control': 'max-age=0',
      'content-type': 'application/x-www-form-urlencoded',
      # 'cookie': 'XSRF-TOKEN=eyJpdiI6IldHODAxRTdybndJTXBWTE1UZTZLblE9PSIsInZhbHVlIjoic095UVZaMnV1QXc1Rk15MVg3TzduMVEwYzhCcFE3YmdmK0RwK0Q5WTNwM2UxTXFOalFrYzlpeXVMYlA4eW1WU0ZNT0hDdEY0Si80UVVIRlY2ZUxRWXFueCtybmFOMFBNSm50d0txOFRtOC9kYWlRQkZPRlZ1Yk9xWkZCTEp4UU0iLCJtYWMiOiI2ZmIwYjg0YTE0MDYzZGU0MmY5NTNjNzFiOTY3ZWMzZTVkYzM4NzkyYmE2MzYwZDE2NjEzYTg4ODhmYjFmN2Y5IiwidGFnIjoiIn0%3D; gdtot_proxy_session=eyJpdiI6IlJLb3cwSEh4VTgxNmtLVnlOK3FLanc9PSIsInZhbHVlIjoiMFRQUnVPY3NsbHUxbm5PaEdYTldTR3NvLzRHck8zZis3cENJSjVmc2pUUE95RTR1cmp0V0Y3U2JMSXo5NVozZUljT29nSHVOZGc5RHBxQVk1REVGb0Z0Q2Vqa2dueUNyMjV0RVIxQXVxaGxZVWRVem9pb2pEUG1TVDd4OExLVy8iLCJtYWMiOiIwODJhMWMyNTM2MTJiZjY4Nzg5MzkyZGU4MzRhMDU3NTkyNDgwMmI0ZWFiMThkNDI5OTRkNjI2NmZmYzNlMDMyIiwidGFnIjoiIn0%3D',
      'origin': 'https://gdbot.xyz',
      'referer': 'https://gdbot.xyz/',
      'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
      'sec-ch-ua-mobile': '?1',
      'sec-ch-ua-platform': '"Android"',
      'sec-fetch-dest': 'document',
      'sec-fetch-mode': 'navigate',
      'sec-fetch-site': 'same-origin',
      'sec-fetch-user': '?1',
      'upgrade-insecure-requests': '1',
      'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36',
  }
  print(f"Trying gdtotv2 for {url}")
  cget = create_scraper().request
  try:
      res = cget('GET', f'https://gdtot.pro/file/{url.split("/")[-1]}')
  except Exception as e:
      raise DirectDownloadLinkException(f'ERROR: {e.__class__.__name__}')
  token_url = etree.HTML(res.content).xpath("//a[contains(@class,'inline-flex items-center justify-center')]/@href")
  if not token_url:
      try:
          url = cget('GET', url).url
          p_url = urlparse(url)
          res = cget("GET",f"{p_url.scheme}://{p_url.hostname}/ddl/{url.split('/')[-1]}")
      except Exception as e:
          raise DirectDownloadLinkException(f'ERROR: {e.__class__.__name__}')
      drive_link = re.findall(r"myDl\('(.*?)'\)", res.text)
      if drive_link and "drive.google.com" in drive_link[0]:
          return drive_link[0]
      else:
          raise DirectDownloadLinkException('ERROR: Drive Link not found, Try in your broswer')
  token_url = token_url[0]
  try:
      token_page = cget('GET', token_url)
  except Exception as e:
      raise DirectDownloadLinkException(f'ERROR: {e.__class__.__name__} with {token_url}')
  path = findall('\("(.*?)"\)', token_page.text)
  if not path:
      raise DirectDownloadLinkException('ERROR: Cannot bypass this')
  path = path[0]
  raw = urlparse(token_url)
  final_url = f'{raw.scheme}://{raw.hostname}{path}'
  title,gdrive = gdflixola(final_url)
  return gdrive
    
@app.route('/api', methods=['GET'])
def get_url():
    url = username = request.args.get('url')
    if 'gdtot' in url:
        title,gdrive_link = gdtotv3(url)
        data = {'title': 'Ye1lowFlash,
            'gdrive':gdrive_link}
        return jsonify(data)
    else:
        title,gdrive_link = gdflixola(url)
        data = {'title': title,
                'gdrive':gdrive_link}
        return jsonify(data)


@app.route('/')
def hello_world():
    return "{'status':'working'}"

if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')
