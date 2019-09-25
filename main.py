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
        'limit': 100,
        'score': 1000
    },
    'week': {
        'time': 'week',
        'limit': 700,
        'score': 2000
    },
    'month': {
        'time': 'month',
        'limit': 3000,
        'score': 4000
    },
    'year': {
        'time': 'year',
        'limit': 36500,
        'score': 8000
    },
    'all': {
        'time': 'all',
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

    def __init__(self, bot, subreddit, settings):
        self.bot = bot
        self.subreddit = subreddit
        self.settings = settings
        self.src_link = self.get_src_img()
        self.tile_links = self.get_tile_imgs()
        self.src_path, self.tile_paths = self.download_imgs()

    def get_src_img(self):
        url = f'https://www.reddit.com/r/{self.subreddit}/about/.json'
        source = ('local', 'img_def.png')
        try:
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
        except requests_e.HTTPError as http_err:
            print(f'{http_err}')
        except requests_e.Timeout as timeout_err:
            print(f'{timeout_err}')
        except requests_e.TooManyRedirects as redirect_err:
            print(f'{redirect_err}')
        return source

    def get_tile_imgs(self):
        img_ext = ('.jpg', '.png', '.jpeg')
        tiles = []
        sr = self.bot.subreddit(self.subreddit)
        idx = 0
        for submission in sr.top(self.settings['time'], limit=self.settings['limit']):
            if not submission.selftext and submission.url.endswith(img_ext):
                if submission.score >= self.settings['score']:
                    if not submission.over_18:
                        print(submission.score, end=' ')
                        print(submission.url)
                        tiles.append((idx, submission.url))
                        idx += 1
        return tiles

    def download_imgs(self):
        def download(img_path, img_fn):
            try:
                r = requests.get(img_path, timeout=30)
                r.raise_for_status()
                if r.status_code == 200:
                    open(img_fn, 'wb').write(r.content)
            except requests_e.ConnectionError as connect_err:
                print(f'{connect_err}')
            except requests_e.HTTPError as http_err:
                print(f'{http_err}')
            except requests_e.Timeout as timeout_err:
                print(f'{timeout_err}')
            except requests_e.TooManyRedirects as redirect_err:
                print(f'{redirect_err}')

        if os.path.exists('img_src'):
            shutil.rmtree('img_src')
        if os.path.exists('img_in'):
            shutil.rmtree('img_in')
        if os.path.exists('img_out'):
            shutil.rmtree('img_out')
        os.mkdir('img_src')
        os.mkdir('img_in')
        os.mkdir('img_out')

        tile_paths = []

        if self.src_link[0] == 'remote':
            src_path = 'img_src/img_src.{e}'.format(e=self.src_link[1].split('.')[-1])
            download(self.src_link[1], src_path)
        else:
            shutil.copyfile('img_def.png', 'img_src/img_def.png')
            src_path = 'img_src/img_def.png'
        for tile in self.tile_links:
            tile_path = 'img_in/{i}.{e}'.format(i=tile[0], e=tile[1].split('.')[-1])
            tile_paths.append(tile_path)
            download(tile[1], tile_path)
        return src_path, tile_paths

    def tune(self, tile_ratio, tile_width, enlargement, reuse, color_mode):
        print("")

    def auto_tune(self):
        print("")

    def make(self):
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
        print("")


def mosaic(bot, subreddit, settings):
    def get_src_img(sub):
        url = f'https://www.reddit.com/r/{sub}/about/.json'
        source = ('local', 'img_def.png')
        try:
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
        except requests_e.HTTPError as http_err:
            print(f'{http_err}')
        except requests_e.Timeout as timeout_err:
            print(f'{timeout_err}')
        except requests_e.TooManyRedirects as redirect_err:
            print(f'{redirect_err}')
        return source

    def get_tile_imgs(sub):
        img_ext = ('.jpg', '.png', '.jpeg')
        tiles = []
        sr = bot.subreddit(subreddit)
        idx = 0
        for submission in sr.top(settings['time'], limit=settings['limit']):
            if not submission.selftext and submission.url.endswith(img_ext):
                if submission.score >= settings['score']:
                    if not submission.over_18:
                        print(submission.score, end=' ')
                        print(submission.url)
                        tiles.append((idx, submission.url))
                        idx += 1
        return tiles

    def download_imgs(src, tiles):
        def download(img_path, img_fn):
            try:
                r = requests.get(img_path, timeout=30)
                r.raise_for_status()
                if r.status_code == 200:
                    open(img_fn, 'wb').write(r.content)
            except requests_e.ConnectionError as connect_err:
                print(f'{connect_err}')
            except requests_e.HTTPError as http_err:
                print(f'{http_err}')
            except requests_e.Timeout as timeout_err:
                print(f'{timeout_err}')
            except requests_e.TooManyRedirects as redirect_err:
                print(f'{redirect_err}')

        if os.path.exists('img_src'):
            shutil.rmtree('img_src')
        if os.path.exists('img_in'):
            shutil.rmtree('img_in')
        if os.path.exists('img_out'):
            shutil.rmtree('img_out')
        os.mkdir('img_src')
        os.mkdir('img_in')
        os.mkdir('img_out')

        tile_paths = []

        if src[0] == 'remote':
            src_path = 'img_src/img_src.{e}'.format(e=src[1].split('.')[-1])
            download(src[1], src_path)
        else:
            shutil.copyfile('img_def.png', 'img_src/img_def.png')
            src_path = 'img_src/img_def.png'
        for tile in tiles:
            tile_path = 'img_in/{i}.{e}'.format(i=tile[0], e=tile[1].split('.')[-1])
            tile_paths.append(tile_path)
            download(tile[1], tile_path)
        return src_path, tile_paths

    src = get_src_img(subreddit)
    tiles = get_tile_imgs(subreddit)
    src_path, tile_paths = download_imgs(src, tiles)
    create_mosaic(
        source_path=src_path,
        target="img_out/img_out.png",
        tile_paths=tile_paths,
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
        itm_type = input("Type (all, top, hot, new, controversial)? ")
        itm_limit = input("Time (hour, day, week, month, year, all)? ")
        itm_score = input("Minimum karma? ")
        setting = {
            'type': itm_type,
            'limit': itm_limit,
            'score': itm_score
        }

    rmm = RedditMosaicMaker(reddit_bot, input_sub, setting)
    rmm.make()

    # mosaic(reddit_bot, input_sub, setting)


if __name__ == "__main__":
    main()
