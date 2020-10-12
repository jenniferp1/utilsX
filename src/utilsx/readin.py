# find other in-house packages in directory path
import os, sys, inspect

currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe()))
)
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# import standard Python packages
import yaml
import re
import glob
import chardet
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


"""
# Functions
"""

def checkdir(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
    return


def check_last_load(url, key_phrase):

    urls, names = scan_csv_list(url)
    new_date = None
    pos = -999
    for i, name in reversed(list(enumerate(names))):
        if name[:4].isdigit():
            new_date = date_in_str(key_phrase["pattern"],key_phrase["last_date"],name)
            if new_date:
                pos = i
                break

    if pos >= 0:
        url = urls[pos]
    else:
        url = None
    return url


def date_in_str(pattern, prev_date, string):

    if re.match(pattern, string):
        m = re.match(pattern, string).group(0)
        if m > prev_date:
            return m
    return None


def get_absolute_path(url, doc_url):
    return urljoin(url,doc_url)


def most_recent(filedir):
    file = max(glob.iglob(filedir),key=os.path.getmtime)
    return file


def read_yaml(params):

    # params list with yaml file name, header

    file_name = params[0]
    header = params[1]

    try:
        with open(file_name) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        return data[header]
    except Exception as error:
        print("\nError in reading user supplied yaml")
        print(error)
        print("Exiting....")
        exit()


def scan_csv_list(url):
    # https://stackoverflow.com/questions/60924860/python-get-list-of-csv-files-in-public-github-repository
    # Issue request: r => requests.models.Response
    r = requests.get(url)

    # Extract text: html_doc => str
    html_doc = r.text

    # Parse the HTML: soup => bs4.BeautifulSoup
    soup = BeautifulSoup(html_doc, 'html.parser')

    # Find all 'a' tags (which define hyperlinks): a_tags => bs4.element.ResultSet
    a_tags = soup.find_all('a')

    # Store a list of urls ending in .csv: urls => list
    urls = ['https://raw.githubusercontent.com'+re.sub('/blob', '', link.get('href'))
            for link in a_tags  if '.csv' in link.get('href')]

    # Store a list of file names
    list_names = [url.split('.csv')[0].split('/')[url.count('/')] for url in urls]

    return urls, list_names


def unicodify(seq, min_confidence=0.5):
    # https://stackoverflow.com/questions/14856872/check-encoding-and-convert-to-unicode
    guess = chardet.detect(seq)
    if guess["confidence"] < min_confidence:
        # chardet isn't confident enough in its guess, so:
        raise UnicodeDecodeError

    return seq.decode(guess["encoding"])
