#!/usr/bin/env python3
'''The _The Flat Hat_ article scraper.

``Let's hope their site NEVER EVER changes.''

Usage:
    fhscrape [options] <yyyy>
    fhscrape --help

<yyyy>     Year's archive to scrape.
-m <mm>    Scrape archive for a month [default: all].
-h --help  Show this screen.
--version  Show version.

'''
VERSION = "0.1.0"

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from string import digits, ascii_letters, punctuation
from os import makedirs
from docopt import docopt

def soupFromURL(url: str) -> "BS4 object":
    ffua = "Science"
    request = Request(url, headers={"User-Agent": ffua})

    with urlopen(request) as response:
        html = response.read().decode("utf-8")

    return BeautifulSoup(html)

def log(*s, indent=0):
    s = " ".join(s)
    s = " " * indent * 2 + s
    if len(s) > 80:
        s = s[:77] + "..."
    if len(s) < 80:
        s += ' ' * (80 - len(s))
    print(s, end="\r")

def logClear():
    print(" " * 80, end="\r")

def linksInMonthArchive(month: str, year: str) -> ["url"]:
    print("Scraping the Flat Hat archive for {}/{}, hang on...".format(month, year))
    monthArchiveURL = "http://flathatnews.com/{}/{}/".format(year, month)

    page = 1
    allArticles = []
    while True:
        try:
            soup = soupFromURL("{}page/{}/".format(monthArchiveURL, page))
            articles = [ article_div.find("h3").a["href"]for article_div
                         in soup.find_all("div", class_="list_category") ]
            allArticles.extend(articles)
            log("Got page {}.".format(page), indent=1)
            page += 1
        except:
            break

    articleCount = len(allArticles)
    if articleCount == 0:
        print("Nothing to see!")
        return

    pluralPage = '' if page == 1 else 's'
    pluralArticle = '' if articleCount == 1 else 's'
    m = "{} page{} of archived articles scraped. Got {} article URL{}."
    print(m.format(page, pluralPage, articleCount, pluralArticle))
    return allArticles

def linksInYearArchive(year: str) -> ["url"]:
    print("Scraping the Flat Hat archive for the year {}, hang on...".format(year))

    allArticles = []
    article = object()
    for month in range(1, 13):
        articles = linksInMonthArchive(month, year)
        if articles is None:
            break
        allArticles.extend(articles)

    articleCount = len(allArticles)
    pluralArticle = '' if articleCount == 1 else 's'
    print("Altogether got {} article{} from {}.".format(articleCount, pluralArticle, year))
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
    def __init__(self, body, title, author, date, time):
        self.body = body
        self.title = title
        self.author = author
        self.date = date
        self.time = time

    def __repr__(self):
        return "<Article: _{}_>".format(self.title)

    @classmethod
    def download(cls, url):
        soup = soupFromURL(url)
        title = soup.find("h1").string
        author = soup.find("a", rel="author").string
        body = soup.find("div", class_="pure_content").get_text()

        time = soup.find("span", class_="timestamp")
        date = time.find_previous_sibling().string
        time = time.string

        log(title, indent=1)
        return cls(body, title, author, date, time)

    def save(self):
        filename = "fh_archive/{}.txt".format(toPosix(self.title))
        log(filename, indent=1)
        lines = [self.title, self.author, ""]
        lines.extend(self.body)
        with open(filename, 'w') as f:
            f.writelines(lines)

if __name__ == "__main__":
    args = docopt(__doc__, version=VERSION)
    month, year = args["-m"], args["<yyyy>"]
    if month == "all":
        links = linksInYearArchive(year)
    else:
        links = linksInMonthArchive(month, year)
    logClear()
    print("Downloading articles...")
    articles = [ Article.download(link) for link in links ]
    logClear()
    print("Articles downloaded, now saving to disk...")
    makedirs("fh_archive", exist_ok=True)
    for article in articles:
        article.save()
    logClear()
    print("Articles probably saved, if so they definitely live in the fh_archive/ directory.")
