from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler

from deliv import counter


def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart)
    crawler.start()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)


    # concrete deliverable part
    print(f'Number of unique pages: {len(counter._url_list)}')
    longest_words, longest_url = counter.getLongest()
    print(f'Longest page: {longest_url}, {longest_words} words')

    print('50 most common words:')
    for word, count in counter.getRank50():
        print(f"{word}: {count}")

    print('Subdomains:')
    for subdomain, count in sorted(counter._url_page_count.items()):
        if ".uci.edu" in subdomain:
            print(f"{subdomain}, {count}")