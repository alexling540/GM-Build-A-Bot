import configparser

username, password = None, None

clientID = input("Client ID? ")
clientSecret = input("Client Secret? ")
userAgent = input("User Agent? ")
readAccess = True if (input("[OPT] Read Access (requires username and password)? [Y/N] ").lower() == 'y') else False
if readAccess:
    username = input("Username? ")
    password = input("Password? ")

cfg = configparser.ConfigParser()
cfg['PRAW'] = {
    'ClientID': clientID,
    'ClientSecret': clientSecret,
    'UserAgent': userAgent
}
if readAccess:
    cfg['Reddit'] = {
        'Username': username,
        'Password': password
    }

with open("praw.ini", 'w') as cfgFile:
    cfg.write(cfgFile)
