## Build-A-Bot
**Dependencies**
- PRAW
- ConfigParser
- Pillow
- PySide2
- [mosaic](https://github.com/dvdtho/python-photo-mosaic) by dvdtho
  - scikit-image
  - numpy
  
**Set up**
1. Clone this repo
2. Download all the dependencies
3. Make a reddit account (or use an existing one)
4. [Create an app](https://www.reddit.com/prefs/apps/)
   1. Name it whatever you want
   2. Select `script`
   3. Add a description
   4. Add a redirect url (it can be http://127.0.0.1)
   5. Click `create app`
5. Run `IniConfig.py` or `IniConfigGUI.py`
   1. Input the `ClientID`, found below "personal use script"
   2. Input the `ClientSecret`, found above "name"
   3. Input the `UserAgent`, this can be whatever you want
6. `praw.ini` should be created
7. You can now use `main.py`
8. Follow the prompts in the console
