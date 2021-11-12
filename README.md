# scrape-google-query

This repo holds some scripts for scraping documents from a google query. For example, say you want
to find examples of University Codes of Conduct. You could go to Google and search for: "university
code of conduct pdf", and you would get a mix of different filetypes and webpages. If you add to
that query "filetype:pdf", you will get a bunch of results where the link is to a pdf hosted on
some server. This tool is for scraping those links, and downloading the files.

This tool also provides a scrappy review tool for going through the downloaded files and removing
any files which are not up to your standards. For example, maybe some documents are not relevant
to your query, and you want to get rid of them. Going through 300 documents by hand can be a chore, 
so review_docs handles opening the files and prompting you for whether or not the file is relevant. 
You can also add a note about a document, for later review. The review tool was built for Debian-based
linux distros and is not guaranteed to work on other distros. The things that will break are the location
of the Trash directory and the command to open the default app. Those are set to the following:

* Trash location: `~/.local/share/Trash/files`
* Default app opener: `xdg-open`

and can be changed easily in review.py after cloning.

These could also easily be modified for MacOS. 

## Getting Started

1. Clone the repo
2. Run `$ python scrape.py --help` (example: `$ python scrape.py 250 data/conduct "university code of conduct"`)
3. Wait
4. Run `$ python review.py --help` (continuing with example: `$ python review.py data/conduct`)

## `scrape.py`

```
usage: scrape.py [-h] [--filetype FILETYPE] [--domain DOMAIN]
                 num_docs save_dir query

Scrape university codes of conduct from google search. Uses BeautifulSoup to
scrape a list of pdf URLs from a google search looking for university codes of
conduct.

positional arguments:
  num_docs              maximum number of docs to download
  save_dir              where to save docs
  query                 query string

optional arguments:
  -h, --help            show this help message and exit
  --filetype FILETYPE, -f FILETYPE
                        file extension to look for. Do not include period.
                        e.g. 'pdf'
  --domain DOMAIN, -d DOMAIN
                        Google domain to use. Defaults to .com
```

## `review.py`

```
usage: review.py [-h] [--responses] data_path

Use metadata file to open documents for review, and delete irrelevant docs.

positional arguments:
  data_path        path to data to review

optional arguments:
  -h, --help       show this help message and exit
  --responses, -r  display valid responses and exit
```

### Valid responses to prompt

After each document is opened, the user will be prompted: `Is this doc relevant? >`. These are the valid responses and what they do:

Hint: run `$ python review.py -r` to see this in CLI

| Response | Alternative(s) | Description & Action |
|:---------:|:------------:|-----------------------|
| `yes` | `y` | Document is relevant: set `reviewed` key to `True`
| `no` | `n` | Document is not relevant: remove from metadata and move file to trash
| `reopen` | `r` | Open the current document again.
| `mistake` | `m` | You replied `y`/`n` when you meant the opposite: user is prompted for which of the last 5 docs was a mistake. That document is readded to the metadata as unreviewed, and if the file is in the trash it is restored.
| `note`, `comment` | `c` | Add a note to the current document
| `quit` | `q` | Save progress and quit
