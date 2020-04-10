import scrapy
from datetime import datetime as dt
import pprint
import json
DATETIME_FORMAT_INPUT='%Y-%m-%dt%H%M%S%z' #2020-04-08t23:00:00+01:00 <- example of datetime in news item
BASE_URL = "https://cointelegraph.com/"
API_URL = "api/v1/content/json/_tp?"
TAGS = ['bitcoin', 'ripple', 'ethereum', 'litecoin']

class CoinTelegraphSpider(scrapy.Spider):
    name = "coin_telegraph"
    headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:74.0) Gecko/20100101 \
            Firefox/74.0',
            'cookies' : {}
    }
    def start_requests(self):
        urls = [BASE_URL+"tags/"+tag for tag in TAGS]
        url_json_response = [BASE_URL+API_URL+ "page=" + str(i) + "&tag=" + tag + "&lan=en"\
                            for i in range(2,4) for tag in TAGS]

        for url in urls:
            yield scrapy.Request(url=url, headers=self.headers, callback=self.parse_news_webpage)

        for url in url_json_response:
            yield scrapy.Request(url=url, method="POST", headers=self.headers,callback=self.parse_api_response)

    def parse_news_webpage(self, response):
        #get the list of links we need for the news
        news_list = response.css('li.post-preview-list-inline__item')
        for news_item in news_list:
            link = news_item.css('div.post-preview-item-inline article.post-preview-item-inline__article \
                                a::attr(href)').get().strip()
            title = news_item.css('div.post-preview-item-inline article.post-preview-item-inline__article \
                div.post-preview-item-inline__content header.post-preview-item-inline__header \
                div.post-preview-item-inline__title-wrp a span::text').get().strip()
            #follow the link to get the actual content of the new
            if link is not None:
                yield response.follow(link, headers=self.headers, callback=self.parse_new)

        #request for the api for more news (it only allows us to ask for page 2, 3 and 4 of the news)


    def parse_api_response(self, response):
        json_response = json.loads(response.body_as_unicode())
        for new in json_response["posts"]["recent"]:
            yield response.follow(new["url"], headers=self.headers, callback=self.parse_new)

    def parse_new(self,response):
        if response.status != 200:
            yield {
                'status': 0,
                'response_code': response.status
            }
        else:
            post = response.css('div.post-area')[0]
            id = int(response.xpath('/html/head/meta[@property="instant-view:news_page"]/@content').get())
            #obtain attributes of the new
            datetime = post.css('div.post-header div.date::attr(datetime)').get()
            if datetime:
                datetime = datetime.replace(':','')
                datetime = dt.strptime(datetime, DATETIME_FORMAT_INPUT)
            author = post.css('div.post-header div.staff div.name a::text').get().strip()
            title = post.css('div.post-header h1.header::text').get().strip()
            description = post.css('div.post-header p.post-description::text').get().strip()

            #obtain the content of the new
            content = []
            paragraphs = post.xpath('//div[contains(@class,"post-content")]/div[contains(@class,"post-full-text")]/*[self::p or self::h2]')
            #paragraphs = post.css('div.post-content div.post-full-text p')
            if paragraphs:
                for paragraph in paragraphs:
                    #check if it's the caption of an image. image captions have an inline style
                    style = paragraph.css('::attr(style)')
                    if style:
                        continue

                    text = paragraph.css('::text')
                    if not text:
                        continue
                    #check if the text is splitted. (this usually happens because of <a> tags)
                    if len(text) > 1:
                        #join the splitted text and then remove the last character
                        text = ''.join(text.getall()).strip()
                    else:
                        text = text.get().strip()

                    content.append(text) 

            #obtain the tags related to the new
            tags = [tag.strip() for tag in post.css('div.tags ul li a::text').getall()]

            #TODO: get the related news and follow
            yield {
                'status':1,
                'id_new': id,
                'title' : title,
                'author' : author,
                'datetime' : datetime,
                'description': description,
                'content': content,
                'tags' : tags,
                'url': response.request.url,
            }