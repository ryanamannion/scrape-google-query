"""Scrape university codes of conduct from google search.

Uses BeautifulSoup to scrape a list of pdf URLs from a google search looking
for university codes of conduct.
"""
import re
import argparse
import json
from tqdm import tqdm
import urllib
from urllib.parse import urlparse
from urllib import request
from pathlib import Path
from bs4 import BeautifulSoup
import requests
import concurrent.futures
from datetime import datetime

BASE_URL = "https://www.google."
repls = {"%20": "_",
         "2B": "+",
         "(": "",
         ")": ""
          }
metadata = {}


def scrape_page(url, href_target, doc_type):
    """Scrape the page at `url` for hyperlinks to document files.
    Args:
        url: URL string for Google search results page
        href_target: Compiled regex to use for matching results' href attr
        doc_type: File extension for document type, no period
    Return:
        List of dictionaries, each containing information about a particular
        document.
    """
    docs = []
    response = requests.get(url)
    if response.status_code != 200:
        raise SystemExit(f"Got response: {response.status_code}")
    soup = BeautifulSoup(response.text, "html.parser")
    result_tags = soup.find_all(href=re.compile(fr"\.{doc_type}"))
    for result_tag in result_tags:
        try:
            url_match = href_target.search(result_tag.attrs['href']).group()
            doc_url = url_match.replace("%2520", "%20")
            raw_fname = doc_url.split('/')[-1]
            [(raw_fname := raw_fname.replace(orig, repl)) for orig, repl 
                                                          in repls.items()]
            hostname = urlparse(doc_url).hostname.split('.')[-2]
            save_fname = hostname+'-'+raw_fname
            if save_fname in metadata:
                continue
            doc = {'url': doc_url,
                   'hostname': hostname,
                   'raw_fname': raw_fname,
                   'save_fname': save_fname,
                   'notes': [],
                   'reviewed': False,
                   'query': "",             # filled in later
                   'download_dt': None}     # filled in later
            docs.append(doc)
        except AttributeError:
            continue
    return docs


def traverse_pages(start_url, href_target, doc_type, n, page_timeout_iters=15):
    """Download documents from `start_url` and each consecutive page.
    Args:
        start_url: URL of desired start page of Google search results
        href_target: Compiled regex to use for matching results' href attr
        doc_type: File extension for document type, no period
        n: Max number of desired documents (max: 1000)
        page_timeout_iters: After this number of attempted pages with no change
          in the number of documents found, quit the loop. This happens when
          there are fewer than `n` documents in the results
    Return:
        List of dictionaries, each containing information about a particular
        document. This is all the documents for each page given to scrape_page
    """
    page_start = "&start={}"
    url_format = start_url + page_start
    print("Scraping...")
    scraped = []
    next_url = start_url
    n_found = 0       # count how many we have found
    n_found_last_time = None
    same = 0
    start = 0       # for moving to the next page
    while len(scraped) < n and start < 1000:
        docs = scrape_page(next_url, href_target, doc_type)
        scraped.extend(docs)
        start += 10
        next_url = url_format.format(start)
        n_found_last_time = n_found
        n_found = len(scraped)
        if n_found == n_found_last_time:
            # break if we stop getting more docs for 5 pages in a row
            same += 1
            if same > page_timeout_iters:
                break
        print(f"Found: {n_found}", end='\r')
    print(f"Found: {n_found}")
    return scraped


def download_document(doc, save_dir):
    """Downloads a document to save_dir
    Args:
        doc: Dict of information about a document, created in `scrape_page()`
        save_dir: Path to save directory. Does not need to exist
    """
    url = doc['url']
    save_dir = Path(save_dir)
    save_path = save_dir / doc['save_fname']
    urllib.request.urlretrieve(url, save_path)
    if save_path.exists():
        doc['download_dt'] = datetime.utcnow().isoformat()
        metadata[str(doc['save_fname'])] = doc
    else:
        print(f"Could not download: {url}")


def assemble_query(query, filetype):
    """Assemble plaintext query and filetype in google parseable query."""
    query = "/search?q="+query.lower().replace(" ", "+")
    if filetype:
        query = query+f"+filetype:{filetype.lower()}"
    return query


def main(query_str, filetype, domain, n_docs, save_dir):
    """Download n number of docs to `save_dir`.
    Uses Query given at the top of the file. Should probably make that
    changeable with CLI
    """
    global metadata
    # prep data
    if not save_dir.exists():
        save_dir.mkdir(parents=True)
    metadata_path = save_dir / "metadata.json"
    if metadata_path.exists():
        with open(str(metadata_path), 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}

    # get doc URLs
    query_url_part = assemble_query(query_str, filetype)
    start_url = BASE_URL + domain.lstrip('.') + query_url_part
    href_target = re.compile(f"https://.*\.{filetype}")
    docs = traverse_pages(start_url, href_target, filetype, n_docs)

    # download docs from URLs
    futures = []
    for doc in tqdm(docs, desc="Downloading documents"):
        # `doc` here is a dict
        doc['query'] = query_str
        with concurrent.futures.ThreadPoolExecutor() as executor:
            func_args = [doc, save_dir]
            futures.append(executor.submit(download_document, *func_args))
    concurrent.futures.wait(futures)

    # save metadata to file
    with open(str(metadata_path), 'w') as f:
        json.dump(metadata, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("num_docs", type=int, help="maximum number of docs to "
                                                   "download")
    parser.add_argument("save_dir", type=Path, help="where to save docs")
    parser.add_argument("query", type=str, help="query string")
    parser.add_argument("--filetype", "-f", type=str, default="pdf",
                        help="file extension to look for. Do not include"
                             " period. e.g. 'pdf'")
    parser.add_argument("--domain", "-d", type=str, default=".com",
                        help="Google domain to use. Defaults to .com")
    args = parser.parse_args()

    main(query_str=args.query,
         filetype=args.filetype.lstrip('.'),
         domain=args.domain,
         n_docs=args.num_docs,
         save_dir=args.save_dir)

    urllib.request.urlcleanup()
