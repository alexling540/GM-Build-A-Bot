import praw
import configparser
import requests
import requests.exceptions as requests_e
import os
import shutil
import mosaic
from PIL import Image
from math import sqrt

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


class RedditMosaicMaker:

    def __init__(self, bot=None, subreddit=None, settings=None):
        self.bot = bot
        self.subreddit = subreddit
        self.settings = settings
        self.src_link, self.tile_links, self.src_path, self.tile_paths = None, None, None, None
        self.__status_src__, self.__status_tiles__, self.__status_config__ = 0, 0, 0
        self.__config__ = [mosaic.Config(tile_ratio=1920//800, tile_width=300, enlargement=20, color_mode='RGB'), True]

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
            print("SOURCE: Using default image... \n└\t",
                  f'{connect_err}')
            print("\t")
        except requests_e.HTTPError as http_err:
            print("SOURCE: Using default image... \n└\t",
                  f'{http_err}')
        except requests_e.Timeout as timeout_err:
            print("SOURCE: Using default image... \n└\t",
                  f'{timeout_err}')
        except requests_e.TooManyRedirects as redirect_err:
            print("SOURCE: Using default image... \n└\t",
                  f'{redirect_err}')

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
            print("TILES: Unable to fetch images \n└\t",
                  f'{value_error}')
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
            print("DOWNLOAD: Download failed, skipping... \n└\t",
                  f'{connect_err}')
            return -1
        except requests_e.HTTPError as http_err:
            print("DOWNLOAD: Download failed, skipping... \n└\t",
                  f'{http_err}')
            return -1
        except requests_e.Timeout as timeout_err:
            print("DOWNLOAD: Download failed, skipping... \n└\t",
                  f'{timeout_err}')
            return -1
        except requests_e.TooManyRedirects as redirect_err:
            print("DOWNLOAD: Download failed, skipping... \n└\t",
                  f'{redirect_err}')
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
            except OSError as os_error:
                print("SOURCE: Unable to delete old directory / new directory \n└\t",
                      f'{os_error}')
                self.__status_src__ = -2
            else:
                self.src_path = src_path
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
                self.__status_tiles__ = -2
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
                        print(f'TILES: Failed to download {tile}')
                print("TILES: Downloaded {num} of {den} images".format(num=idx, den=len(self.tile_links)))
                self.tile_paths = tile_paths
                self.__status_tiles__ = 2
        else:
            print("TILES: Image links not found")

    def set_config(self, config, reuse=False):
        if self.__status_src__ == 2 and self.__status_tiles__ == 2:
            src = mosaic.SourceImage(self.src_path, config)
            msc = mosaic.MosaicImage(src.image, "img_out/img_out.png", config)
            if msc.total_tiles > len(self.tile_paths):
                reuse = True

            nConfig = mosaic.Config(
                tile_ratio=config.tile_ratio,
                tile_width=int(round(config.tile_width)),
                enlargement=int(round(config.enlargement))
            )

            self.__config__ = (nConfig, reuse)
            self.__status_config__ = 1
        else:
            print("CONFIG: No Source / Tiles found, cannot config")

    def auto_config(self):
        try:
            src = Image.open(self.src_path)
            src_w, src_h = src.size
            tile_ratio = src_w / src_h
            enlargement = 1920 // src_w
            tile_width = sqrt((1920 / tile_ratio) * (1920 / len(self.tile_paths))) / 2

            cfg = mosaic.Config(tile_ratio=tile_ratio, tile_width=tile_width, enlargement=enlargement)
            self.set_config(cfg, False)
        except IOError as io_error:
            print("CONFIG: Source image could not be opened \n└\t",
                  f'{io_error}')
        except AttributeError as attr_error:
            print("CONFIG: Source image does not exist \n└\t",
                  f'{attr_error}')
        finally:
            src.close()

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
            if self.__status_config__ == 0:
                print("MAKE: No config found, using default config")
            mosaic.create_mosaic(
                source_path = self.src_path,
                target      = "img_out/img_out.png",
                tile_paths  = self.tile_paths,
                tile_ratio  = self.__config__[0].tile_ratio,
                tile_width  = self.__config__[0].tile_width,
                enlargement = self.__config__[0].enlargement,
                reuse       = self.__config__[1],
                color_mode  = self.__config__[0].color_mode
            )
        else:
            fail_case = "Unknown"
            if self.__status_src__ == -1:
                fail_case = "get_src_img"
            elif self.__status_src__  == -2:
                fail_case = "download_src"
            elif self.__status_tiles__ == -1:
                fail_case = "get_tile_imgs"
            elif self.__status_tiles__ == -2:
                fail_case = "download_tiles"
            print(f"MAKE: Make failed, try {fail_case} again")


def main():
    reddit_bot = init_bot()
    input_sub = input("SUBREDDIT? ")
    settings = input("Settings? (day, week, month, year, all, custom) ")
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
    rmm.get_src_img()
    rmm.get_tile_imgs()
    rmm.download_src()
    rmm.download_tiles()
    rmm.auto_config()
    rmm.make()


if __name__ == "__main__":
    main()
