import praw
import configparser
import requests
import os
from PIL import Image
from mosaic import create_mosaic

SETTINGS = {
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

    #if 'Reddit' in cfg:
    #    redditBot = praw.Reddit(client_id=cfg['PRAW']['ClientID'],
    #                            client_secret=cfg['PRAW']['ClientSecret'],
    #                            user_agent=cfg['PRAW']['UserAgent'],
    #                            username=cfg['Reddit']['Username'],
    #                            password=cfg['Reddit']['Password'])
    #else:
    #    redditBot = praw.Reddit(client_id=cfg['PRAW']['ClientID'],
    #                            client_secret=cfg['PRAW']['ClientSecret'],
    #                            user_agent=cfg['PRAW']['UserAgent'])
    reddit_bot = praw.Reddit(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
                             user_agent=USER_AGENT)

    return reddit_bot


def get_images(r_bot, subreddit, setting=None):
    if setting is None:
        setting = SETTINGS['week']
    url = "https://www.reddit.com/r/{sub}/about/.json".format(sub=subreddit)
    r_get = requests.get(url, headers={'User-agent': USER_AGENT})
    r_data = r_get.json()['data']
    source = None
    if r_data['header_img'] != "":
        source = r_data['header_img']
    elif r_data['banner_background_image'] != "":
        source = r_data['banner_background_image']
    elif r_data['icon_img'] != "":
        source = r_data['icon_img']

    print(source)

    img_ext = ('.jpg', '.png', '.jpeg')
    imgs = []
    sr = r_bot.subreddit(subreddit)
    for submission in sr.top(setting['type'], limit=setting['limit']):
        if not submission.selftext and submission.url.endswith(img_ext):
            if submission.score >= setting['score']:
                if not submission.over_18:
                    print(submission.score, end=' ')
                    print(submission.url)
                    imgs.append(submission.url)
    return source, imgs


def download_imgs(source, imgs):
    def dl(img, fn):
        r = requests.get(img)
        with open(fn, 'wb') as f:
            f.write(r.content)

    if source is None:
        src_path = 'img_def.png'
    else:
        src_fn = 'img_src/img_src.{e}'.format(e=source.split('.')[-1])
        r = requests.get(source)
        with open(src_fn, 'wb') as f:
            f.write(r.content)
        src_path = src_fn

    paths = []
    idx = 0
    for img in imgs:
        img_fn = 'img_in/{n}.{e}'.format(n=idx, e=img.split('.')[-1])
        r = requests.get(img)
        with open(img_fn, 'wb') as f:
            f.write(r.content)
        paths.append(img_fn)
        idx += 1
    return src_path, paths


def auto(src_path, img_paths):
    n_paths = len(img_paths)
    src_w, src_h = Image.open(src_path, 'r').size
    tile_ratio = src_h/src_w
    10 * (src_w / n_paths)
    enlargement = 1920/src_w
    tile_width, reuse = None, None
    return tile_ratio, tile_width, enlargement, reuse


def main():
    reddit_bot = init_bot()
    input_sub = input("SUBREDDIT? ")
    settings = input("Settings? ")
    custom = None
    if settings == "custom":
        itm_type = input("Type (all, top, hot, new, controversial)? ")
        itm_limit = input("Time (hour, day, week, month, year, all)? ")
        itm_score = input("Minimum karma? ")
        custom = {
            'type': itm_type,
            'limit': itm_limit,
            'score': itm_score
        }
    if not os.path.exists('img_src'):
        os.mkdir('img_src')
    if not os.path.exists('img_in'):
        os.mkdir('img_in')
    if not os.path.exists('img_out'):
        os.mkdir('img_out')
    src, imgs = get_images(reddit_bot, input_sub, custom)
    src_path, paths = download_imgs(src, imgs)

    create_mosaic(
        source_path="{src}".format(src=src_path),
        target="img_out/img_out.png",
        tile_paths=paths,
        # tile_ratio=1920/800,
        # tile_width=300,
        # enlargement=20,
        # reuse=True,
        # color_mode='RGB'
    )


if __name__ == "__main__":
    main()
