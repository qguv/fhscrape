#!/usr/bin/env python3

from pathlib import Path

class Article:
    '''Generic article. Works for FH or Squat.'''

    def __init__(self, body: str, author=None, title=None, date=None, time=None):
        self.body = body
        self.title = title
        self.author = author

        if date is None:
            self.datetime = None
        elif time is None:
            self.datetime = datetime.strptime(date.strip(), "%B %d, %Y%I:%M %p") 
        else:
            self.datetime = datetime.strptime(date.strip() + time.strip(), "%B %d, %Y%I:%M %p") 

    def __repr__(self):
        return "<Article: _{}_>".format(self.title)

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
            print("Error:", e)
            print()
            return

    def log(self, status=None, indent=0):
        if status is None:
            log(title, indent=indent)
        else:
            log(status, self.title, indent=indent)

class FHArticle(Article):
    '''FH article. Can be scraped from a given URL or loaded from a file.'''

    def __repr__(self):
        return '<FH Article: "{}">'.format(self.title[:40] + "...")

    @classmethod
    def unsafe_download(cls, url):
        soup = soupFromURL(url)
        title = soup.find("h1").string
        author = soup.find("a", rel="author").string
        body = soup.find("div", class_="pure_content").get_text()

        time = soup.find("span", class_="timestamp")
        date = soup.find("div", class_="the_date").find_all("p")[1].string
        time = time.string

        return cls(body, author, title, date, time)
    
    @classmethod
    def download(cls, url):
        try:
            return cls.unsafe_download(url)
        except Exception as e:
            print("\nWARNING: An article download failed.")
            print("URL:", url)
            print("Error:", e)
            print()
            return

    @classmethod
    def load(cls, path: Path):
        with path.open('r') as f:
            lines = [ s.strip() for s in f.readlines() ]
        title, author, body = lines[0], lines[1], '\n'.join(lines[3:])
        return cls(body, author, title)

class SquatArticle(Article):
    '''Squat article. Can be loaded from a file.'''

    def __repr__(self):
        return "<Squat Article by {}>".format(self.author)

def splitByStartCondition(superlist, predicate):
    '''Split a list by a predicate that should begin each list.

      even = lambda x: x % 2 == 0
      sublistSplit([1, 2, 3, 4, 5], even) == [[1], [2, 3], [4, 5]]'''

    sublistStart = current = 0
    last = len(superlist)
    for current, element in enumerate(superlist):
        if predicate(element):
            yield superlist[sublistStart:current]
            sublistStart = current

def readSquatArticles() -> (SquatArticle):
    SQUAT_PATH = "corpora/squat.txt"
    with (Path(__file__).parent / SQUAT_PATH).open('r') as f:
        lines = [ s.strip() for s in f.readlines() ]
    for article in splitByStartCondition(lines, lambda line: line.startswith("BY ")):
        if not article:
            continue
        author, body = article[0].strip(), '\n'.join(article[1:])
        author = author[3:] # remove 'BY '
        yield SquatArticle(body, author)

def readFHArticles() -> (FHArticle):
    for f in Path(__file__).parent.glob("corpora/fh_*/*/*.txt"):
        yield FHArticle.load(f)

squat = list(readSquatArticles())
flathat = list(readFHArticles())
