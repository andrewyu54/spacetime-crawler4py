from bs4 import BeautifulSoup
from urllib.parse import urlsplit, urlunsplit
import re
from threading import Lock

STOPWORDS = {"a","about","above","after","again","against","all","am","an","and","any","are","aren't","as","at","be","because","been","before","being","below","between","both","but","by","can't","cannot","could","couldn't","did","didn't","do","does","doesn't","doing","don't","down","during","each","few","for","from","further","had","hadn't","has","hasn't","have","haven't","having","he","he'd","he'll","he's","her","here","here's","hers","herself","him","himself","his","how","how's","i","i'd","i'll","i'm","i've","if","in","into","is","isn't","it","it's","its","itself","let's","me","more","most","mustn't","my","myself","no","nor","not","of","off","on","once","only","or","other","ought","our","ours","ourselves","out","over","own","same","shan't","she","she'd","she'll","she's","should","shouldn't","so","some","such","than","that","that's","the","their","theirs","them","themselves","then","there","there's","these","they","they'd","they'll","they're","they've","this","those","through","to","too","under","until","up","very","was","wasn't","we","we'd","we'll","we're","we've","were","weren't","what","what's","when","when's","where","where's","which","while","who","who's","whom","why","why's","with","won't","would","wouldn't","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"}

class Counter:
    
    def __init__(self) -> None:
        self._url_list = set()    # BASE RESOURCE only
        self._word_count = {}     # word->count, across all urls
        self._page_word_count = {}
        self._url_page_count = {}     # url -> number of pages under it
        self._under_uci = 0       # number of subdomains under uci.edu domain
        
        self._longest = (-1, "")    # (number, url)
        
        # Thread safety lock
        self._lock = Lock()
        
    
    def checkUrlIn(self, url: str) -> bool:
        # scheme, netloc, path, query, fragment
        parts = urlsplit(url)
        clean_url = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ''))
        with self._lock:
            return (clean_url in self._url_list)
    
    @staticmethod
    def cleanUrl(url: str) -> str:
        parts = urlsplit(url)
        clean_url = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ''))
        return clean_url
    
    def _updatePageWordNumber(self, url, resp) -> int:
        # added this to handle empty response
        if resp.raw_response is None:
            return 0
        
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        text = soup.get_text(separator=' ').lower()
        tokenlist = re.sub(r'[^a-z0-9\s]', ' ', text).split()
        tokenlist = [x for x in tokenlist if x not in STOPWORDS]
        for token in tokenlist:
            self._word_count[token] = self._word_count.get(token, 0) + 1
        
        self._page_word_count[url] = len(tokenlist)
        
        return len(tokenlist)
        
    
        
    
    def addUrl(self, url: str, resp):
        parts = urlsplit(url)
        clean_url = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ''))
        
        with self._lock:
            if clean_url in self._url_list:
                return
            self._url_list.add(clean_url)
            
            num = self._updatePageWordNumber(clean_url, resp)
            
            # check .uci.edu
            if parts.netloc.endswith(".uci.edu"):
                self._under_uci += 1
                domain = parts.netloc
                self._url_page_count[domain] = self._url_page_count.get(domain, 0) + 1
            
            # update longest
            if num > self._longest[0]:
                self._longest = (num, url)
            
    def getLongest(self):
        with self._lock:
            return self._longest
    
    def getRank50(self):
        with self._lock:
            wordlist = [(x, y) for x, y in self._word_count.items()]
            wordlist.sort(key=lambda x: x[1], reverse=True)
            return wordlist[:50]
    
        
counter = Counter()