# onemanga

## About

A platform where manga, manhuwa, and other type of comic readers can collectively add them and check their latest chapter updates when they are available.

> Current Version is completely a self-hosting based.

## Supported Site

- [x] [AsuraToon](https://asuratoon.com/)
- [ ] [ManhuaPlus](https://manhuaplus.com/)
- [ ] [Manga Demon](https://mgdemon.org/)
- [ ] [VyVy Manga](https://vymanga.net/) (Cloudflare connection issues)
- [ ] [MAngaFire](https://mangafire.to/home)


## Features

- Add the link of the book to track
- Check the manga status, if the manga is available anymore or not (IN PROGRESS)
- Ability to add same name book URLS to a one BOOK for easier tracking (TODO)
- Check the lastest updated chapters on main page
- Auto track the last read chapter or set the last read chapter 
- Import/Export the available manga data for Anilist like services

## Installation

1. Clone the repository
2. Set the `.env` file in home directory with key-value like in `sample.env`
3. Run locally using `flask --app main --host=0.0.0.0 --debug run`

### Made with

- Python 3.12
- Flask
- Jinja3
- Sqlite
- Beautiful Soup 
