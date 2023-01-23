from urllib import request
import requests
from lxml import etree
import json


class Anime:
    def __init__(self, url):
        if requests.get(url).status_code == 404:
            self.url = None
            return
    
        html = request.urlopen(url)
        contents = html.read().decode()

        et = etree.fromstring(contents, parser=etree.HTMLParser())
        titles = et.xpath(r'//*[@id="main"]/div')[0]
        
        self.url = url
        self.title = ''
        self.episodes = []
        
        for t in titles.iter():
            # アニメタイトル
            if t.attrib.get('class') == 'com-video-TitleSection__title':
                self.title = t.text
        
            # アイテム
            if t.attrib.get('class') == 'com-content-list-ContentListItem':
                self.episodes.append(EpisodeItem(self, t.getchildren()[0]))


class EpisodeItem:
    def __init__(self, anime, htmldata):
        self.anime = anime
    
        episode_item = htmldata
        content_container = episode_item.getchildren()[0]
        overview = content_container.getchildren()[0]
        
        # URL や タイトル名
        link = overview.getchildren()[0]
        
        # 尺の長さやリリース年
        #supplement = overview.getchildren()[1]
        # なんか取得する際にエラーが出て修正もめんどいのでコメントアウトしました
        
        # サムネイル画像
        thumbnail = content_container.getchildren()[2]\
            .getchildren()[0].getchildren()[0]
        
        self.url = 'https://abema.tv' + link.get('href')
        self.title = link.getchildren()[0].getchildren()[0].text
        #self.length = supplement.getchildren()[0].text
        #self.released_year = supplement.getchildren()[1].text
        self.description = content_container.getchildren()[1].getchildren()[0].text
        self.thumbnail_url = json.loads(thumbnail.getchildren()[1].text).get('url')
        self.free = None

        html = request.urlopen(self.url)
        contents = html.read().decode()
        et = etree.fromstring(contents, parser=etree.HTMLParser())
        titles = et.xpath(r'//*[@id="main"]/div')[0]
        
        for t in titles.iter():
            if t.attrib.get('class') == 'com-video-EpisodeTitleBlock__expire-text':
                VODLabel_text = t.getchildren()[0].getchildren()[0].getchildren()[0].get('class')
            
                if VODLabel_text.endswith('free'):
                    self.free = True
                elif VODLabel_text.endswith('premium'):
                    self.free = False


if __name__ == '__main__':
    # AbemaTVのアニメURLをここに入れる
    anim = Anime('https://abema.tv/video/title/11-46')
    
    print('アニメ: ', anim.title)
    print('='*30)
    
    for ep in anim.episodes:
        print('タイトル: ', ep.title)
        print('無料？: ', str(ep.free))
        print('='*30)
