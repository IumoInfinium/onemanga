import json
import requests

from extractor import AsuraToon

def check_manga_webpage(URL: str) -> bool:
    '''
    Checks the status of webpage availability
    '''
    try:    
        resp = requests.get(URL)

        if resp.status_code != 200:
            return False
        return True
    except ModuleNotFoundError:
        raise Exception("Requests module not found")
    except Exception as e:
        print("Request failed", e)
        return False


def collect_manga_data(url, site, *args, **kwargs) -> dict:
    '''
    Collects manga data details, given the URL and site
    Optional args: chapter_link -> also return key-value for that chapter:chapter-data
    '''

    chapter_link = kwargs.get("chapter_link", None)

    if site == "AsuraToon":
        site_obj = AsuraToon(url)
        if not site_obj.manga_check():
            return {}
        
        manga_info = {}
        
        site_obj.chapter_extractor() 

        # check the extraction success code
        if site_obj.connection_status['code'] != 200:
            return {}
        
        # manga_info['latest_chapter_number'] = site_obj.latest_chapter_by_number()
        manga_info['latest_chapter_time'] = site_obj.latest_chapter_by_time()
        manga_info['latest_chapter_data'] = site_obj.latest_chapter_by_data()
        manga_info['chapters'] = site_obj.chapters
        if chapter_link:
            manga_info['chapter'] = site_obj.get_manga_chapter_data(chapter_link)
        
        print(manga_info.keys())
        # return manga information with latest chapter's time, data and list of chapters
        return manga_info
