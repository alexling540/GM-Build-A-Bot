import configparser
import os


def get_ini(config):
    if os.path.exists('praw.ini'):
        config.read('praw.ini')
        return config['PRAW']['ClientID'], config['PRAW']['ClientSecret'], config['PRAW']['UserAgent']
    return "", "", ""


def save_ini(config, clientID, clientSecret, userAgent):
    config['PRAW'] = {
        'ClientID': clientID,
        'ClientSecret': clientSecret,
        'UserAgent': userAgent
    }
    config.write(open('praw.ini', 'w'))


if __name__ == "__main__":
    cfg = configparser.ConfigParser()
    client_ID, client_secret, user_agent = get_ini(cfg)

    if client_ID == "" or client_secret == "" or user_agent == "":
        client_ID = input("Client ID? ")
        client_secret = input("Client Secret? ")
        user_agent = input("User Agent? ")
    else:
        if input("Change Client ID? [Y/N] ").lower() == 'y':
            client_ID = input("New Client ID? ")
        if input("Change Client Secret? [Y/N] ").lower() == 'y':
            client_secret = input("Client Secret? ")
        if input("Change User Agent? [Y/N] ") == 'y':
            user_agent = input("User Agent? ")

    save_ini(cfg, client_ID, client_secret, user_agent)
