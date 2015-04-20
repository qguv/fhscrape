#!/usr/bin/env python3
'''
Scrapes articles from /The Flat Hat/ archive
Let's hope their site NEVER EVER changes.

Usage:
    fhscrape [options] <yyyy>
    fhscrape [options] --forever
    fhscrape --help

<yyyy>     Year's archive to scrape.
-m <mm>    Scrape archive for a month [default: all].
-d <dir>   Directory to put scraped articles.
--forever  Get everything The Flat Hat's got.
-h --help  Show this screen.
--version  Show version.
'''
VERSION = "1.0.0-dev"

# CLI
from docopt import docopt

# making internet requests
from urllib.request import Request, urlopen
from urllib.error import URLError

# interpreting HTML
from bs4 import BeautifulSoup

# working with files
from os import makedirs

# pythonic misc.
from string import digits, ascii_letters, punctuation
from datetime import datetime, timezone

def soupFromURL(url: str) -> "BS4 object":
    ffua = "Science"
    request = Request(url, headers={"User-Agent": ffua})

    with urlopen(request) as response:
        html = response.read().decode("utf-8")

    return BeautifulSoup(html)

def log(*printables, indent=0):
    '''Prints lines over each other, wrapped to 80 columns.'''

    # build the string to be printed
    s = " ".join([ str(x) for x in printables ])

    # prepend an indent level
    s = " " * indent * 2 + s

    # truncate long lines
    if len(s) > 80:
        s = s[:77] + "..."
    if len(s) < 80:
        s += ' ' * (80 - len(s))

    # print line and move cursor to the beginning again
    print(s, end="\r")

def logClear():
    print(" " * 80, end="\r")

class NotArchivedException(Exception): pass

def linksInArchive(year: str, month: str) -> ["url"]:

    if month == "all":
        month = ''
    else:
        month = '/' + str(month)

    print("Scraping the Flat Hat archive for {}{}, hang on...".format(year, month))
    archiveURL = "http://flathatnews.com/{}{}".format(year, month)

    page = 1
    allArticles = []
    while True:
        try:
            soup = soupFromURL("{}/page/{}/".format(archiveURL, page))
            articles = [ article_div.find("h3").a["href"]for article_div
                         in soup.find_all("div", class_="list_category") ]
            allArticles.extend(articles)
            log("Got page {}.".format(page), indent=1)
            page += 1
        except URLError:
            break

    articleCount = len(allArticles)
    if articleCount == 0:
        raise NotArchivedException("Year not in The Flat Hat database.")

    pluralPage = '' if page == 1 else 's'
    pluralArticle = '' if articleCount == 1 else 's'
    m = "{} page{} of archived articles scraped. Got {} article URL{}."
    print(m.format(page, pluralPage, articleCount, pluralArticle))
    return allArticles

def toPosix(inStr):
    inStr = inStr.replace(' ', '_').lower()

    # Didn't write this bit; don't blame me for its ugliness.
    class Del:
        def __init__(self, keep=digits + ascii_letters + '_'):
            self.comp = dict((ord(c),c) for c in keep)
        def __getitem__(self, k):
            return self.comp.get(k)

    return inStr.translate(Del())

class Article:
    def __init__(self, body: str, title: str, author: str, date: str, time: str):
        self.body = body
        self.title = title
        self.author = author
        self.datetime = datetime.strptime(date + time, "%B %d, %Y%I:%M %p") 

    def __repr__(self):
        return "<Article: _{}_>".format(self.title)

    @classmethod
    def unsafe_download(cls, url):
        soup = soupFromURL(url)
        title = soup.find("h1").string
        author = soup.find("a", rel="author").string
        body = soup.find("div", class_="pure_content").get_text()

        time = soup.find("span", class_="timestamp")
        date = soup.find("div", class_="the_date").find_all("p")[1].string
        time = time.string

        return cls(body, title, author, date, time)
    
    @classmethod
    def download(cls, url):
        try:
            return cls.unsafe_download(url)
        except Exception as e:
            print("\nWARNING: An article download failed.")
            print("URL:", url)
            print(e)
            print()
            return

    def unsafe_save(self, baseDirectory):
        directory = "{}/{}-{}".format(baseDirectory, self.datetime.year, self.datetime.month)
        makedirs(directory, exist_ok=True)
        filename = "{}/{}.txt".format(directory, toPosix(self.title))
        lines = [self.title, self.author, self.body]
        with open(filename, 'w') as f:
            f.writelines((line + '\n' for line in lines))

    def save(self, baseDirectory):
        try:
            self.unsafe_save(baseDirectory)
        except Exception as e:
            print("\nWARNING: An article save failed.")
            print("Title:", self.title)
            print("Date:", self.datetime)
            print(e)
            print()
            return

    def log(self, status=None, indent=0):
        if status is None:
            log(title, indent=indent)
        else:
            log(status, self.title, indent=indent)

def interface(year, month, baseDirectory):
    links = linksInArchive(year, month)
    logClear()
    print("Downloading articles...")

    # preparing to save in fh_archive directory
    makedirs(baseDirectory, exist_ok=True)

    linkCount = len(links)
    for i, link in enumerate(links):
        a = Article.unsafe_download(link) #DEBUG
        a.save(baseDirectory)
        a.log(status="{:.3%}".format(i/linkCount), indent=1)

    logClear()
    print("Articles downloaded and saved to {}/year-month/article_title.txt.".format(baseDirectory))

def forever(baseDirectory):
    '''Get all articles ever from The Flat Hat's online database.'''

    thisYear = datetime.now().year
    for year in range(thisYear, 1693, -1):
        try:
            interface(year, "all", baseDirectory)
        except NotArchivedException:
            if year == thisYear: continue # in case nothing's been published yet this year
            print("You now have the entire available Flat Hat archive: from {} to {}.".format(year, thisYear))
            break

# Docopt Argument Parsing
if __name__ == "__main__":
    try:
        args = docopt(__doc__, version=VERSION)

        # default to directory with timestamp
        if args["-d"] is None:
            args["-d"] = "fh_{}".format(int(datetime.now(timezone.utc).timestamp()))
        if args["--forever"]:
            forever(args["-d"])
        else:
            interface(args["<yyyy>"], args["-m"], args["-d"])
    except KeyboardInterrupt:
        print("\nGot interrupt signal, exiting...")
    except NotArchivedException:
        print("\nThat month/year combination isn't in the Flat Hat archive.")
