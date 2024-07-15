import os
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash
)
import json
import datetime 
from dotenv import load_dotenv
from extractor import AsuraToon

from utils.init_db import get_db_connection, query_db
from utils.db_func import add_manga, get_manga, get_mangas, remove_manga, get_available_updates, update_read_manga, get_manga_chapters, get_manga_by_link, update_manga

from utils.helpers import collect_manga_data

load_dotenv(".env")

app = Flask(__name__)

# averylongsecretkey
app.secret_key = "uwu"

MAIN_TABLE_NAME = os.environ.get("MAIN_TABLE_NAME", "mangas")
MANGA_DATA_TABLE_NAME = os.environ.get("MANGA_DATA_TABLE_NAME", "manga_data")

supported_sites = ['AsuraToon']

@app.route('/')
def homepage():
    mangas = get_available_updates()
    context = {'available' : mangas}

    return render_template("index.html", context = context)

@app.route('/add', methods = ['GET', 'POST'])
def add_manga_page():
    if request.method == "POST":
        # add_manga to the database
        print(request.form)

        manga_name = request.form.get("manga_name", None)
        manga_link = request.form.get("manga_link", None)
        if not manga_name or not manga_link:
            flash('Please check the manga information')
            redirect(url_for("homepage"))

        # extract the manga details from page
        manga_information = collect_manga_data(manga_link, request.form.get('site'))

        print(len(manga_information['chapters']))

        # manga_information = {}, extraction failed
        if not manga_information:
            flash("No manga data")
            return redirect(request.referrer)    

        # add manga details to DB
        output: dict = add_manga(
            request.form.get('manga_name', None),
            request.form.get('manga_link', None),
            request.form.get('site', None),
            last_updated_chapter_metadata = manga_information['latest_chapter_data']['metadata'],
            last_updated_chapter_link = manga_information['latest_chapter_data']['link'],
            last_updated_chapter_time = manga_information['latest_chapter_data']['date'],
            manga_chapters = manga_information['chapters'],
        )
        if not output:
            print("FAILED")
            flash("Sorry, we failed to add this manga, please try again in a few minutes")
            return redirect(request.referrer)
        

        return redirect(url_for('view_page'))
        # return render_template(
        #     "mangas.html",
        #     manga_id = output.get('id'),
        #     context = {
        #         'manga_id':  output.get('id'),
        #         'manga_link': output.get('URL')
        #     })
    
    print(supported_sites)
    return render_template('add_manga.html', context = {
        'supported_sites' :supported_sites,
        "a" : 1,
    })


@app.route('/view', methods = ['GET'])
def view_page():

    context = {}
    context["mangas"] = []

    mangas = query_db("SELECT * FROM mangas", (), False )
    for manga in mangas:
        manga = dict(manga)
        manga_info = {
            'id': manga['id'],
            'name': manga['name'],
            'link': manga['link'],
        }
        print(manga_info['id'])
        context['mangas'].append(manga_info)

    return render_template('mangas.html', context = context)

@app.route('/view/<manga_id>', methods = ['GET'])
def view_manga_page(manga_id):
    context = {}

    manga = get_manga(manga_id)
    print("manga metadata")
    context['manga'] = manga

    # manga_chapters = json.loads(get_manga_chapters(manga_id)['manga_chapters'])
    manga_chapters = get_manga_chapters(manga_id)
    manga_chapters = json.loads(manga_chapters['manga_chapters'])
    print("GOT manga chapters" )
    if not manga_chapters or manga_chapters is None:
        context['chapters'] = []


    context = manga
    context['chapters'] = manga_chapters
    context['supported_sites'] = supported_sites
    # print(context['chapters'][0])
    # map(datetime.datetime.date(), context['chapters']['date'])

    return render_template("manga.html", context = context)

@app.route('/delete/<manga_id>', methods = ['POST', 'GET'])
def delete_manga(manga_id: str = None):
    state = remove_manga(manga_id)
    print(request.json)
    if state == False:
        print("NOT ABLE TO DELETE")
        return {"msg": "Failed to delete", 'code': 500}
    print("DELETED!")

    return {"msg": "Ok", 'code': 200}

@app.route('/updates', methods=['POST'])
def updates():
    # request_body = request.json
    # print(request.json)
    mangas = get_mangas()

    print(len(mangas))
    for manga in mangas:
        print('Processing ....', manga['name'])
        new_manga_details  = collect_manga_data(manga['link'], manga['site'])

        print("NEW MANGA :", new_manga_details['latest_chapter_data']['metadata'] , new_manga_details['latest_chapter_data']['link'])
        print("OLD MANGA :", manga['last_updated_chapter_metadata'], manga['last_updated_chapter_link'])
        
        if new_manga_details['latest_chapter_data']['metadata'] != manga['last_updated_chapter_metadata'] or new_manga_details['latest_chapter_data']['link'] != manga['last_updated_chapter_link']:

            update_manga(
                manga_id = manga['id'], 
                latest_chapter = {
                    'metadata' : new_manga_details['latest_chapter_data']['metadata'],
                    'date': new_manga_details['latest_chapter_data']['date'],
                    # 'num' : new_manga_details['latest_chapter_data']['num'],
                    'link' : new_manga_details['latest_chapter_data']['link'],
                },
                chapters = json.dumps(new_manga_details['chapters'])
            )
    return {'code' : 500}


@app.route('/forward', methods = ['POST'])
def forward_to_manga_link():
    print("GOTACHA")
    if request.method == "POST":
        payload = request.json
        print(payload)

        manga_details = get_manga_by_link(payload['manga_link'])
        print("HELLO")
        if not manga_details or manga_details == {}:
            return {}
        
        manga_chapter = None
        manga_chapters = json.loads(get_manga_chapters(manga_details['id'])['manga_chapters'])
        
        for chapter in manga_chapters:
            if chapter['link'] == payload['manga_chapter_link']:
                manga_chapter = chapter
                break
        if manga_chapter is None:
            print("asd")
            return {}
        
        print(manga_chapter)
        
        read_status = 0

        if  manga_details['last_updated_chapter_link'] == payload['manga_chapter_link'] or \
            manga_details['last_updated_chapter_link'] == manga_details['last_read_chapter_link']:
            read_status = 1

        state = update_read_manga(
            manga_id = payload['manga_id'],
            manga_chapter_link = payload['manga_chapter_link'],
            last_read_chapter_metadata = manga_chapter['metadata'],
            last_read_chapter_time = manga_chapter['date'],
            readed = read_status,
        )    
        
        return { 'msg' : state }
    
    return redirect("homepage")

@app.route('/search', methods = ['POST'])
def search_manga():

    if request.method == "POST":
        payload = request.json
        print(payload)

        if not payload['name']:
            return {}

        all_mangas = get_mangas()

        results = []
        for manga in all_mangas:
            if str(payload['name']).strip().lower() in str(manga['name']).strip().lower():
                results.append({
                    'id' : manga['id'], 
                    'name' : manga['name'], 
                    'link': url_for('view_manga_page', manga_id = manga['id'])
                })
        
        return {
            "result" : results, 
        } 
    return {}

@app.route('/edit/<manga_id>', methods=['POST'])
def edit_manga(manga_id):
    print(request.json)
    if request.method  == "POST":

        payload = request.json

        manga_information = {}
        chapters = {}
        last_read = {}
        last_update = {}

        # check if the main manga_link has been changed
       
        # if payload.get('old_link', None) and payload.get('link') != payload.get('old_link'):
        manga_information = collect_manga_data(payload.get('link'), payload.get('site'))
        chapters = manga_information.get('chapters', None)
        
        print(chapters)
        if chapters and payload.get('last_read_chapter_link_update', None):
            for chapter in chapters:
                print(chapter)
                if chapter['link'] == payload['last_read_chapter_link_update']:
                    last_read = chapter
                    print('LAST READ VARIABLE')
                    break
                
        # dump the chapters
        chapters = json.dumps(chapters)
        print(manga_information['latest_chapter_data'])
        last_update['metadata'] = manga_information['latest_chapter_data']['metadata']
        last_update['link'] = manga_information['latest_chapter_data']['link']
        last_update['date'] = manga_information['latest_chapter_data']['date']

        update_manga(
            manga_id=manga_id, 
            name=payload.get('name',None), 
            link=payload.get('link',None), 
            site=payload.get('site', None),
            chapters = chapters if chapters else None,
            last_read = last_read,
            latest_chapter = last_update if last_update else None,
        )
        # update_manga(
        #     manga_id=manga_id, 
        #     name=payload.get('name', None), 
        #     link=payload.get('link', None), 
        #     site=payload.get('site', None),
        # )
        return {'msg': 'Ok', 'code': 200}

    return {'code': 500, 'msg': 'invalid request'}
if __name__ == "__main__":

    # create table if not exists
    with get_db_connection() as curr:
        curr.execute('PRAGMA foreign_keys = ON')
        curr.execute(f"""
            CREATE TABLE IF NOT EXISTS {MAIN_TABLE_NAME} (
                id varchar PRIMARY KEY,
                name varchar(255),
                link varchar(255),
                site varchar(255),
                last_updated_chapter_metadata varchar(255),
                last_updated_chapter_link varchar(255),
                last_updated_chapter_time REAL,
                last_read_chapter_metadata varchar(255),
                last_read_chapter_link varchar(255),
                last_read_chapter_time REAL,
                read integer,
                created_at REAL,
                updated_at REAL
            )
        """)

        curr.execute(f"""
            CREATE TABLE IF NOT EXISTS {MANGA_DATA_TABLE_NAME} (
                id integer PRIMARY KEY AUTOINCREMENT,
                manga_id varchar(255) NOT NULL,
                manga_chapters TEXT,
                FOREIGN KEY (manga_id) REFERENCES mangas (id)
            )
        """)
    
    app.run(debug=True)