import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import hashlib

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links]


seen_checksums = set()

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
    
    if not resp.raw_response or not resp.raw_response.content:
        return list()
    

    content_type = resp.raw_response.headers.get('content-type', '').lower()
    
    if 'text/html' not in content_type:
        return list()

    try:
        content = resp.raw_response.content


        checksum = hashlib.md5(content).hexdigest()
        if checksum in seen_checksums:
            print(f'Duplicate page detected: {url}')
            return list()
        else:
            seen_checksums.add(checksum)
        
        
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a')
        valids = []


        for link in links:
            href = link.get('href')
            if href is None:
                continue

            href = href.strip()
            if not href:
                continue

            absolute_url = urljoin(resp.url, href)
            absolute_url = absolute_url.split('#')[0].rstrip('/')

            if absolute_url and is_valid(absolute_url):
                valids.append(absolute_url)

        return valids


    except Exception as e:
        return list()



def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.


    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        

        allowed = [
                "ics.uci.edu",
                "cs.uci.edu",
                "informatics.uci.edu",
                "stat.uci.edu",
        ]
        domain = parsed.netloc.lower()
        
        if ':' in domain:
            domain = domain.split(':')[0]
        
        if domain not in allowed:
            return False
        

        url_lower = url.lower()
        trap_patterns = [
            "?do=", "?idx=", "&do=", "&idx=", "?action=", "&action=",
            "?submit=", "&submit=", "?reply=", "&reply="
        ]

        if any(pattern in url_lower for pattern in trap_patterns):
            return False


        path_lower = parsed.path.lower()
        restricted_paths = [
            "calendar", "login", "logout", "signup", "register", 
            "ticket", "display.html", "wp-admin", "admin", "cgi-bin",
            "archive", "download", "attachment"
        ]
        if any(restricted in path_lower for restricted in restricted_paths):
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
        print ("TypeError for ", parsed)
        raise
