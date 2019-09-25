import praw
import configparser
import requests
import requests.exceptions as requests_e
import os
import shutil
from PIL import Image
from mosaic import create_mosaic

POST_SETTINGS = {
    'day': {
        'time': 'day',
        'category': 'top',
        'limit': 100,
        'score': 1000
    },
    'week': {
        'time': 'week',
        'category': 'top',
        'limit': 700,
        'score': 2000
    },
    'month': {
        'time': 'month',
        'category': 'top',
        'limit': 3000,
        'score': 4000
    },
    'year': {
        'time': 'year',
        'category': 'top',
        'limit': 36500,
        'score': 8000
    },
    'all': {
        'time': 'all',
        'category': 'top',
        'limit': 500000,
        'score': 16000
    }
}

CLIENT_ID, CLIENT_SECRET, USER_AGENT = None, None, None


def init_bot():
    cfg = configparser.ConfigParser()
    cfg.read('praw.ini')

    global CLIENT_ID, CLIENT_SECRET, USER_AGENT
    CLIENT_ID = cfg['PRAW']['ClientID']
    CLIENT_SECRET = cfg['PRAW']['ClientSecret']
    USER_AGENT = cfg['PRAW']['UserAgent']

    return praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent=USER_AGENT)


def auto_tune(src_path, img_paths):
    n_paths = len(img_paths)
    src_w, src_h = Image.open(src_path, 'r').size
    tile_ratio = src_h/src_w
    10 * (src_w / n_paths)
    enlargement = 1920/src_w
    tile_width, reuse = None, None
    return tile_ratio, tile_width, enlargement, reuse


class RedditMosaicMaker:

    def __init__(self, bot=None, subreddit=None, settings=None):
        self.bot = bot
        self.subreddit = subreddit
        self.settings = settings
        self.src_link, self.tile_links, self.src_path, self.tile_paths = None, None, None, None
        self.__status_src__, self.__status_tiles__ = 0, 0

    def set_bot(self, bot):
        self.bot = bot

    def set_subreddit(self, sub):
        self.subreddit = sub

    def set_settings(self, settings):
        self.settings = settings

    def get_src_img(self):
        source = ('local', 'img_def.png')
        try:
            url = f'https://www.reddit.com/r/{self.subreddit}/about/.json'
            r_get = requests.get(url, headers={'User-agent': USER_AGENT})
            r_data = r_get.json()['data']
            if r_data['header_img'] != "":
                source = ('remote', r_data['header_img'])
            elif r_data['banner_background_image'] != "":
                source = ('remote', r_data['banner_background_image'])
            elif r_data['icon_img'] != "":
                source = ('remote', r_data['icon_img'])
        except requests_e.ConnectionError as connect_err:
            print(f'{connect_err}')
            print("\tSOURCE: Using default image")
        except requests_e.HTTPError as http_err:
            print(f'{http_err}')
            print("\tSOURCE: Using default image")
        except requests_e.Timeout as timeout_err:
            print(f'{timeout_err}')
            print("\tSOURCE: Using default image")
        except requests_e.TooManyRedirects as redirect_err:
            print(f'{redirect_err}')
            print("\tSOURCE: Using default image")

        self.src_link = source
        self.__status_src__ = 1

    def get_tile_imgs(self):
        img_ext = ('.jpg', '.png', '.jpeg')
        tiles = []

        try:
            sr = self.bot.subreddit(self.subreddit)

            if self.settings['category'] == 'top':
                sub_list = sr.top(self.settings['time'], limit=self.settings['limit'])
            elif self.settings['category'] == 'hot':
                sub_list = sr.hot(self.settings['time'], limit=self.settings['limit'])
            elif self.settings['category'] == 'new':
                sub_list = sr.new(self.settings['time'], limit=self.settings['limit'])
            elif self.settings['category'] == 'controversial':
                sub_list = sr.controversial(self.settings['time'], limit=self.settings['limit'])
            elif self.settings['category'] == 'rising':
                sub_list = sr.rising(self.settings['time'], limit=self.settings['limit'])
            else:  # self.settings['category'] == 'random_rising':
                sub_list = sr.random_rising(self.settings['time'], limit=self.settings['limit'])

            for submission in sub_list:
                if not submission.selftext and submission.url.endswith(img_ext):
                    if submission.score >= self.settings['score']:
                        if not submission.over_18:
                            tiles.append(submission.url)
        except ValueError as value_error:
            print(f'{value_error}')
            print("\tTILES: Unable to fetch images")
            self.__status_tiles__ = -1
        else:
            self.tile_links = tiles
            print("TILES: Fetched {n} images".format(n=len(tiles)))
            self.__status_tiles__ = 1

    def __download__(self, img_path, img_fn):
        try:
            r = requests.get(img_path, timeout=30)
            r.raise_for_status()
            if r.status_code == 200:
                open(img_fn, 'wb').write(r.content)
        except requests_e.ConnectionError as connect_err:
            print(f'{connect_err}')
            return -1
        except requests_e.HTTPError as http_err:
            print(f'{http_err}')
            return -1
        except requests_e.Timeout as timeout_err:
            print(f'{timeout_err}')
            return -1
        except requests_e.TooManyRedirects as redirect_err:
            print(f'{redirect_err}')
            return -1
        else:
            return 0

    def download_src(self):
        if self.__status_src__ >= 1:
            try:
                if os.path.exists('img_src'):
                    shutil.rmtree('img_src')
                os.mkdir('img_src')
                if self.src_link[0] == 'remote':
                    src_path = 'img_src/img_src.{e}'.format(e=self.src_link[1].split('.')[-1])
                    self.__download__(self.src_link[1], src_path)
                else:
                    shutil.copyfile('img_def.png', 'img_src/img_def.png')
                    src_path = 'img_src/img_def.png'
                self.src_path = src_path
            except OSError as os_error:
                print(f'{os_error}')
                print("\tSOURCE: Unable to delete old directory / new directory")
                self.__status_src__ = -1
            else:
                self.__status_src__ = 2
        else:
            print("SOURCE: Image link not found")

    def download_tiles(self):
        if self.__status_tiles__ >= 1:
            try:
                if os.path.exists('img_in'):
                    shutil.rmtree('img_in')
                if os.path.exists('img_out'):
                    shutil.rmtree('img_out')
                os.mkdir('img_in')
                os.mkdir('img_out')
            except OSError as os_error:
                print(f'{os_error}')
                print("TILES: Unable to delete old directory / make new directory")
                self.__status_tiles__ = -1
            else:
                tile_paths = []
                idx = 0
                for tile in self.tile_links:
                    tile_path = 'img_in/{i}.{e}'.format(i=idx, e=tile.split('.')[-1])
                    status = self.__download__(tile, tile_path)
                    if status != -1:
                        tile_paths.append(tile_path)
                        idx += 1
                    else:
                        print(f'TILES: Failed to download {tile_path}')
                print("TILES: Downloaded {num} of {den} images".format(num=idx, den=len(self.tile_links)))
                self.tile_paths = tile_paths
                self.__status_tiles__ = 2
        else:
            print("TILES: Image links not found")

    def tune(self, tile_ratio, tile_width, enlargement, reuse, color_mode):
        pass

    def auto_tune(self):
        pass
        # self.tune()

    def make(self):
        if self.__status_src__ == 0:
            self.get_src_img()
        if self.__status_src__ == 1:
            self.download_src()
        if self.__status_tiles__ == 0:
            self.get_tile_imgs()
        if self.__status_tiles__ == 1:
            self.download_tiles()
        if self.__status_src__ == 2 and self.__status_tiles__ == 2:
            # pass
            create_mosaic(
                source_path=self.src_path,
                target="img_out/img_out.png",
                tile_paths=self.tile_paths,
                # tile_ratio=1920/400,
                tile_width=20,
                enlargement=5,
                # reuse=True
                # color_mode='RGB'
            )


def main():
    reddit_bot = init_bot()
    input_sub = input("SUBREDDIT? ")
    settings = input("Settings? ")
    if settings == 'day':
        setting = POST_SETTINGS['day']
    elif settings == 'week':
        setting = POST_SETTINGS['week']
    elif settings == 'month':
        setting = POST_SETTINGS['month']
    elif settings == 'year':
        setting = POST_SETTINGS['year']
    elif settings == 'all':
        setting = POST_SETTINGS['all']
    else:
        itm_time = input("Time (hour, day, week, month, year, all)? ")
        itm_cat = input("Category (all, top, hot, new, controversial)? ")
        itm_limit = input("Max no. of images? ")
        itm_score = input("Minimum karma? ")
        setting = {
            'time': itm_time,
            'category': itm_cat,
            'limit': itm_limit,
            'score': itm_score
        }

    # rmm = RedditMosaicMaker()
    rmm = RedditMosaicMaker(reddit_bot, input_sub, setting)
    rmm.make()


if __name__ == "__main__":
    main()
