import os
import uuid
import time
import json

from dotenv import load_dotenv
from datetime import datetime

from extractor import AsuraToon
from utils.init_db import get_db_connection, query_db
from utils.helpers import check_manga_webpage
# Database Static Vars

load_dotenv('.env')

MAIN_TABLE_NAME=os.environ.get("MAIN_TABLE_NAME", "mangas")
MANGA_DATA_TABLE_NAME = os.environ.get("MANGA_DATA_TABLE_NAME", "manga_data")

print(MAIN_TABLE_NAME, MANGA_DATA_TABLE_NAME)

def add_manga(name: str, URL: str, site: str, **kwargs):
    '''
    Add manga information to database
    '''
    last_updated_chapter_link = kwargs.get("last_updated_chapter_link", "NULL")
    last_updated_chapter_metadata = kwargs.get("last_updated_chapter_metadata", "NULL")
    last_updated_chapter_time = kwargs.get("last_updated_chapter_time", 0)
    manga_chapters = kwargs.get("manga_chapters" , {})

    try:
        if not site or not URL:
            return {}
        
        if not check_manga_webpage(URL):
            print("Page does not exists")
            return {}

        generated_id = uuid.uuid1()
        current_time_epochs = time.time()

        # string dump all the chapters related data
        manga_chapters_text = json.dumps(manga_chapters)
        

        
        # get the last element in the `manga_chapters` array
        print("LAST CHAPTER ----")
        last_chapter_data = manga_chapters[-1]

        with get_db_connection() as conn:

            conn.execute(f"""
                INSERT INTO {MAIN_TABLE_NAME}
                (
                    id, name, link, site,
                    last_updated_chapter_metadata, last_updated_chapter_link, last_updated_chapter_time,
                    last_read_chapter_metadata, last_read_chapter_link, last_read_chapter_time, 
                    read, created_at, updated_at
                )
                VALUES
                (
                    '{generated_id}', '{name}', '{URL}', '{site}',
                    '{last_updated_chapter_metadata}', '{last_updated_chapter_link}', {last_updated_chapter_time}, 
                    '{last_chapter_data['metadata']}', '{last_chapter_data['link']}', {last_chapter_data['date']},
                    0, {current_time_epochs}, {current_time_epochs}
                )"""
            )
            # add manga_chapter details to MANGA_DATA_TABLE_NAME
            query = f"""INSERT INTO {MANGA_DATA_TABLE_NAME}(manga_id, manga_chapters)
                VALUES ('{generated_id}', '{manga_chapters_text}')
            """
            print(query)
            conn.execute(query)
            
            # optional - context manager handles it, but still added 
            conn.commit()

            return {
                "id" : generated_id,
                "name": name,
                "URL": URL,
                "site": site,
                "read" : 0,
                "created_at": current_time_epochs,
                "updated_at": current_time_epochs,
            }
    except Exception as e:
        print("ERROR :", e)
        return {}
    
def get_mangas():
    # get the `id` of all the mangas
    try:
        output = query_db(
            query=f"SELECT * from {MAIN_TABLE_NAME}",
            args=(),
            one=False
        )
        return output
    except:
        raise Exception("Failed to get data")

def get_manga(manga_id: str = "") -> dict:
    # get manga information given its `id`
    # return {} if `manga_id` not provided
    if not manga_id: 
        return {}
    
    try:
        return query_db(
            f"SELECT * FROM {MAIN_TABLE_NAME} WHERE id = '{manga_id}'", (), True
        )
    except Exception as e:  
        print("Failed to get the data", e)
        return {}

def get_manga_chapters(manga_id: str = None) -> dict : 
    if not manga_id:
        return {}
    
    try:
        output = query_db(
            f"SELECT manga_chapters FROM {MANGA_DATA_TABLE_NAME} WHERE manga_id = '{manga_id}'", (), True
        )
        return output
    except Exception as e:
        print(e)
        # raise Exception("Failed to get data", e)
        return {}
    

def remove_manga(manga_id: str = None):
    # remove the manga using the `id`
    if not manga_id:
        return False
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('BEGIN')
            cur.execute(f"DELETE FROM {MANGA_DATA_TABLE_NAME} where manga_id = '{manga_id}'", ())
            cur.execute(f"DELETE FROM {MAIN_TABLE_NAME} where id = '{manga_id}'", ())
            conn.commit()
            return True

    except Exception as exec: 
        raise Exception(f"Problem while removing manga from DB: {exec}")
    

def update_read_manga(manga_id: str, manga_chapter_link: str, last_read_chapter_metadata: str, last_read_chapter_time: int, readed: int = 0) -> bool:

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()

            query = f"""UPDATE {MAIN_TABLE_NAME} SET last_read_chapter_link = ?, last_read_chapter_time = ?, last_read_chapter_metadata  = ?, read = ? WHERE id = ?"""
            cur.execute(query, (manga_chapter_link, last_read_chapter_time, last_read_chapter_metadata, readed, manga_id))
            conn.commit()

            return True
    except:
        print("Failed to update the database for read manga")   
        return False
    
def update_manga(manga_id: str, latest_chapter: dict = None, last_read: dict = None, **kwargs):
    '''
    Optional args: `name`, `site`, `link`, `latest_chapter`, `chapters`
    '''
    # data for last updated chapter
    chapters = kwargs.get('chapters', None)
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("begin")
            query = f"UPDATE {MAIN_TABLE_NAME} SET "
            if kwargs.get("site", None):
                query += f"site = '{kwargs.get("site")}', "
            
            if kwargs.get('name', None):
                query += f"name = '{kwargs.get('name')}', "

            if kwargs.get('link', None):
                query += f"link = '{kwargs.get('link')}', "
            
            if latest_chapter:
                # update latest chapters
                if latest_chapter.get('metadata', None):
                    query += f"last_updated_chapter_metadata = '{latest_chapter.get('metadata')}', "

                if latest_chapter.get('link', None):
                    query += f"last_updated_chapter_link = '{latest_chapter.get('link')}', "

                if latest_chapter.get('date', None):
                    query += f"last_updated_chapter_time = {latest_chapter.get('date')}, "
                
                # update read status in DB
                query += " read = 0, "

                if chapters :
                    cur.execute(f"UPDATE {MANGA_DATA_TABLE_NAME} SET manga_chapters = '{chapters}' WHERE manga_id = '{manga_id}'")

            if last_read:
                # update last read chapters
                if latest_chapter.get('metadata', None):
                    query += f"last_read_chapter_metadata = '{last_read.get('metadata')}', "

                if latest_chapter.get('link', None):
                    query += f"last_read_chapter_link = '{last_read.get('link')}', "

                if latest_chapter.get('date', None):
                    query += f"last_read_chapter_time = {last_read.get('date')}, "
                
            # removing the extra `,` in the end of the query
            query = query[:-2]
            query += f" WHERE id = '{manga_id}'"
            print(query)
            cur.execute(query)
            conn.commit()
            
            return get_manga(manga_id)
    except Exception as e:

        print(e)
        return {}
    
def get_available_updates():
    # checks the database to see if the last read chapter link is equal to last updated chapter
    # if they are different, then update is available
    try:
        with get_db_connection() as conn:
            curr = conn.cursor()
            query = f"""
                SELECT id, name, link, site, last_updated_chapter_metadata, last_updated_chapter_link, last_read_chapter_metadata, last_read_chapter_link from {MAIN_TABLE_NAME} where read = 0
            """
            curr.execute(query, ())
            output = curr.fetchall()
            if len(output) == 0:
                return []

            return output
    except Exception as e:
        raise Exception("Cannot read the data from the database", e)
    

def get_manga_by_link(manga_link: str) -> dict:
    """
    Get manga details using link
    Args:  `manga_link` -> link to search for
    """
    try:
        return query_db(f"""
            SELECT * FROM {MAIN_TABLE_NAME} where link = '{manga_link}'
        """, (), True)
    except:
        return {}