import bs4
import requests
import datetime as dt

class AsuraToon:
    def __init__(self, url):
        self.url = url
        self.page_content = None
        self.chapters = None
        self.connection_status = {}
    def manga_check(self):
        resp = requests.get(self.url)

        if resp.status_code != 200:
            return False
        return True

    def extract_page_content(self):
        page_content = requests.get(self.url).text
        self.page_content = page_content
    
    def chapter_extractor(self):
                    
        website_state = self.manga_check()

        if not website_state:
            return {'data' : [], 'code' :404, 'msg': 'Page not found'}
        
        try:
            if self.page_content is None:
                print('Setting Page Content')
                self.extract_page_content()

            soup_obj = bs4.BeautifulSoup(self.page_content,"html.parser")

            chapterlist_obj = soup_obj.find(id="chapterlist")
            chapters_obj = chapterlist_obj.find_all('li')

            chapters = []
            
            for chapter_obj in chapters_obj:
                chapter_link = chapter_obj.find('a').get('href')
                chapter_num, chapter_date = chapter_obj.find_all('span')

                # chapter_num is in format of "Chapter X <chapter metadata (OPTIONAL)>"
                # chapter_date is in format of "June 24, 2023"

                # store the information link
                chapter_metadata = chapter_num.string
                chapter_num = str(chapter_metadata).strip()
                chapter_date = str(chapter_date.string).strip()
                
                try:
                    chapter_num = float(chapter_num.split(" ")[1])
                except:
                    chapter_num = -1
                
                chapters.append({
                    "num": chapter_num, 
                    "metadata": chapter_metadata,
                    "date": dt.datetime.strptime(str(chapter_date), "%B %d, %Y").timestamp(), 
                    "link": chapter_link
                })

            self.connection_status['code'] = 200
            self.connection_status['msg'] = 'OK'

            self.chapters = chapters
            return chapters
        
        except Exception as e:
            self.connection_status['code'] = 500
            self.connection_status['msg'] = f"Failed to extract data from {self.url}.  MESSAGE : {e}"
            self.chapters = {}
            return {}
        


    def latest_chapter_by_data(self, check_new: bool = False):
        if self.chapters is None or check_new:
            self.chapter_extractor()

        if self.connection_status['code'] != 200:
            print(self.connection_status['msg'])
            return {}
        
        return self.chapters[0]

    def latest_chapter_by_number(self, check_new: bool = False):
        if self.chapters is None or check_new:
            self.chapter_extractor()

        if self.connection_status['code'] != 200:
            print(self.connection_status['msg'])
            return {}

        output =  sorted(self.chapters, key = lambda obj: obj['num'], reverse=True)
        return output[0]
        
    def latest_chapter_by_time(self, check_new: bool = False):
        if self.chapters is None or check_new:
            self.chapter_extractor()

        if self.connection_status['code'] != 200:
            print(self.connection_status['msg'])
            return {}
        
        output = sorted(self.chapters, key =lambda obj : obj['date'], reverse=True)
        return output[0]
        
    def get_manga_chapter_data(self, search_link: str) -> dict:
        if self.chapters is None:
            self.chapter_extractor()

        if self.connection_status['code'] != 200:
            print(self.connection_status['msg'])
            return {}
        
        for chapter in self.chapters:
            if chapter['link'] == search_link:
                return chapter
        return {}
    

if __name__ == "__main__":
    url1 = "https://asuratoon.com/manga/1908287720-boundless-necromancer/"

    url2 = "https://asuratoon.com/manga/1908287720-the-greatest-estate-developer/"
    url3 = "https://asuratoon.com/manga/1908287720-terminally-ill-genius-dark-knight/"
    url4 = "https://asuratoon.com/manga/1908287720-helmut-the-forsaken-child/"
    url4 = "https://asuratoon.com/manga/1908287720-regressing-with-the-kings-power/"
    m1 = AsuraToon(url1)

    m1.extract_page_content()
    m1.chapter_extractor()
    print("PAGE CONTENT", m1.page_content)
    print("CHAPTERS", m1.chapters)
    
    print(m1.latest_chapter_by_data(True))
    print("NUMNERS ::")
    print(m1.latest_chapter_by_number(True))

    print("TIME ::")
    print(m1.latest_chapter_by_time(False))
    