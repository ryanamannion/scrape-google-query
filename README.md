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
linus distros and is not guaranteed to work on other distros. The things that will break are the location
of the trash and the command to open the default app. Those are set to the following:

* Trash location: `~/.local/share/Trash/files`
* Default app opener: `xdg-open`

These could also easily be modified for MacOS. 

## Getting Started

1. Clone the repo
2. Run `$ python scrape.py --help` (example: `$ python scrape.py 250 data/conduct "university code of conduct"`)
3. Wait
4. Run `$ python review.py --help` (continuing with example: `$ python review.py data/conduct`)