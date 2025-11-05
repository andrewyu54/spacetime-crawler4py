# Now in Cody's branch
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
import hashlib

from deliv import counter


# code from https://topic.alibabacloud.com/a/implementation-of-simhash-algorithm-in-python_1_34_33046577.html
class Simhash(object):
    def __init__(self, tokens, hashbits=128):
        self.hashbits = hashbits
        self.tokens = tokens
        self.fingerprint = self.simhash()

    def _string_hash(self, source):
        if source == "":
            return 0
        else:
            x = ord(source[0]) << 7
            m = 1000003
            mask = 2 ** self.hashbits - 1
            for c in source:
                x = ((x * m) ^ ord(c)) & mask
            x ^= len(source)
            if x == -1:
                x = -2
            return x

    def simhash(self):
        v = [0] * self.hashbits
        for t in self.tokens:
            h = self._string_hash(t)
            for i in range(self.hashbits):
                bitmask = 1 << i
                if h & bitmask:
                    v[i] += 1
                else:
                    v[i] -= 1
        fingerprint = 0
        for i in range(self.hashbits):
            if v[i] >= 0:
                fingerprint |= 1 << i
        return fingerprint

    def hamming_distance(self, other_hash):
        x = self.fingerprint ^ other_hash.fingerprint
        tot = 0
        while x:
            tot += 1
            x &= x - 1
        return tot

    def __str__(self):
        return str(self.fingerprint)



seen_urls = set()

def scraper(url, resp):
    if url in seen_urls:
        return list()
    if resp.status != 200:
        return list()
    if resp.raw_response is None:
        return list()
    if resp.raw_response.content is None:
        return list()
    content_type = resp.raw_response.headers.get('content-type', '').lower()
    if 'text/html' not in content_type:
        return list()
    
    counter.addUrl(url, resp)
    seen_urls.add(url)
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]



simhashes = set()


def extract_next_links(url, resp):
    #
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    if resp.status != 200:
        return list()

    content_type = resp.raw_response.headers.get('content-type', '').lower()
  
    if 'text/html' not in content_type:
        return list()
    

    try:
        content = resp.raw_response.content
        
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a')
        valids = []


        # simhash operation
        text = soup.get_text(separator = ' ').lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)

        tokens = text.split()
        simhash = Simhash(tokens)

        for otherhash in simhashes:
            if simhash.hamming_distance(otherhash) <  5:
                print('NEAR DUPLICATE DETECTED!!!')
                return list()
        simhashes.add(simhash)



        for link in links:
            href = link.get('href')
            if href is None:
                continue

            href = href.strip()
            if not href:
                continue

            absolute_url = urljoin(resp.url, href)
            absolute_url = urldefrag(absolute_url)[0]
            absolute_url = absolute_url.rstrip('/')

            if is_valid(absolute_url):
                valids.append(absolute_url)

        return valids


    except Exception as e:
        print('EXCEPTION OCCURRED\n')
        return list()



def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.


    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(['http', 'https']):
            return False
        

        allowed = [
                'ics.uci.edu',
                'cs.uci.edu',
                'informatics.uci.edu',
                'stat.uci.edu',
        ]
        domain = parsed.netloc.lower().split(':')[0]
        
        if not any(domain == a or domain.endswith('.' + a) for a in allowed):
            return False
        



        path = parsed.path.lower()
        restricted_paths = [
            'calendar', 'event', 'events', 'commit', 'pix', 'tags', 'tree', 'doku.php'
        ]
        if any(restricted in path for restricted in restricted_paths):
            return False
        

        query = parsed.query.lower()
        blocked_params = [
            'do=', 'tab_', 'image=', 'idx=', 'C=', 'O=', 'action=',
            'controller=', 'commit=', 'view=', 'from=', 'precision=',
            'p=', 'page_id=', 'share=', 'redirect_to='
        ]
        if any(param in query for param in blocked_params):
            return False
        


        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ('TypeError for ', parsed)
        raise
