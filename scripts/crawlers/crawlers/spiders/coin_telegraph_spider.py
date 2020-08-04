import scrapy
from datetime import date, datetime as dt
from scrapy.exceptions import CloseSpider
import pprint
import json
from random import randint

#DATETIME_FORMAT_INPUT='%b %d, %Y' #"Apr 16, 2020" <- example of datetime in news item
DATETIME_FORMAT_INPUT='%Y-%m-%d' #"2020-07-03" <- example of datetime in news item
BASE_URL = "https://cointelegraph.com/"
API_URL = "api/v1/content/json/_tp?"
TAGS = ['bitcoin','ripple', 'ethereum', 'litecoin']
USER_AGENTS = ['Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en-us) AppleWebKit/419.2.1 (KHTML, like Gecko) Safari/419.3',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:74.0) Gecko/20100101 Firefox/74.0',
                'Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en) AppleWebKit/521.32.1 (KHTML, like Gecko) Safari/521.32.1',
                'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/312.8.1 (KHTML, like Gecko) Safari/312.6',
                'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en_CA) AppleWebKit/125.4 (KHTML, like Gecko) Safari/125.9',
                'Opera/9.80 (Windows NT 6.0; U; en) Presto/2.8.99 Version/11.10',
                'Opera/9.80 (Windows NT 6.1; Opera Tablet/15165; U; en) Presto/2.8.149 Version/11.1',
                'Opera/9.80 (Windows NT 6.1; U; pl) Presto/2.6.31 Version/10.70',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.65 Safari/535.11',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Ubuntu/11.04 Chromium/17.0.963.56 Chrome/17.0.963.56 Safari/535.11',
                'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.66 Safari/535.11',
                'Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13',
                'Mozilla/5.0 (Macintosh; U; Mac OS X 10_5_7; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/ Safari/530.5',
                'Mozilla/5.0 (X11; U; Linux i686; rv:1.7.3) Gecko/20040914 Firefox/0.10',
                'Mozilla/5.0 (X11; U; Gentoo Linux x86_64; pl-PL) Gecko Firefox',
                'Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en-US; rv:1.8.1.13) Gecko/20080313 Firefox'
            ]
API_SEARCH='api/v1/content/search/result?' #for bulk insertion

class CoinTelegraphSpider(scrapy.Spider):
    name = "coin_telegraph"
   
    def get_headers(self):
        headers = {
            'User-Agent': USER_AGENTS[randint(0,len(USER_AGENTS)-1)]
        }
        return headers

    def start_requests(self):
        urls = [BASE_URL+"tags/"+tag for tag in TAGS]
        url_json_response = [BASE_URL+API_URL+ "page=" + str(i) + "&tag=" + tag + "&lan=en"\
                            for i in range(2,4) for tag in TAGS]
        for url in urls:
            headers = {
                'User-Agent': USER_AGENTS[randint(0,len(USER_AGENTS)-1)]
            }
            yield scrapy.Request(url=url, headers=self.get_headers(), callback=self.parse_news_webpage)

        for url in url_json_response:
            headers = {
                'User-Agent': USER_AGENTS[randint(0,len(USER_AGENTS)-1)]
            }
            yield scrapy.Request(url=url, method="POST", headers=self.get_headers(),callback=self.parse_api_response)

    def parse_news_webpage(self, response):
        #get the list of links we need for the news
        news_list = response.css('li.posts-listing__item')
        print(news_list)
        for news_item in news_list:
            link = news_item.css('article.post-card-inline a.post-card-inline__figure-link::attr(href)').get().strip()
            #follow the link to get the actual content of the new
            if link is not None:
                yield response.follow(link, headers=self.get_headers(), callback=self.parse_new)

        #request for the api for more news (it only allows us to ask for page 2, 3 and 4 of the news)


    def parse_api_response(self, response):
        json_response = json.loads(response.body_as_unicode())
        for new in json_response["posts"]["recent"]:
            yield response.follow(new["url"], headers=self.get_headers(), callback=self.parse_new)

    def parse_new(self,response):
        if response.status != 200:
            yield {
                'status': 0,
                'response_code': response.status
            }
        else:
            post = response.css('div.post-page__item')

            if post:
                post = post[0]
                # #obtain attributes of the new
                id = int(post.xpath('//div[contains(@class, "post-page__article")]/article[contains\
                    (@class, "post__article")]/@id').get().split('-')[1])
                author = post.css('div.post-page__article article.post__article div.post-meta\
                    div.post-meta__author a.post-meta__author-link div::text').get().strip()
                datetime = post.css('div.post-page__article article.post__article div.post-meta div.post-meta__publish-date time::attr(datetime)').get().strip()              
                datetime = dt.strptime(datetime, DATETIME_FORMAT_INPUT)
                title = post.css('div.post-page__article article.post__article h1.post__title::text').get().strip()
                description = post.css('div.post-page__article article.post__article p.post__lead::text').get().strip()

                #obtain the content of the new
                content = []
                paragraphs = post.xpath('//div[contains(@class, "post-page__article")]/article[contains\
                    (@class, "post__article")]/div[contains(@class, "post__content-wrapper")]/\
                    div[contains(@class, "post-content")]/*[self::p or self::h3 or self::blockquote]')

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

                # #obtain the tags related to the new
                tags = [tag.strip() for tag in post.css('div.tags-list ul li a::text').getall()]


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
            else:
                yield {
                    'status': 3,
                    'response_code': response.status
                }

class CoinTelegraphSpiderBulk(scrapy.Spider):
    name = "coin_telegraph_bulk"
    pages = {'bitcoin':15,'ethereum': 10, 'ripple': 10,'litecoin': 10}

    def get_headers(self):
        headers = {
            'User-Agent': USER_AGENTS[randint(0,len(USER_AGENTS)-1)]
        }
        return headers

    def start_requests(self):
        for tag in TAGS:
            for i in range(1, self.pages[tag] + 1):
                yield scrapy.Request(url=BASE_URL+API_SEARCH+"query='" + tag + "'&page=" + str(i),
                                    headers=self.get_headers(), callback=self.parse_search_api_response,
                                    method="POST"
                                    )
    #request for the api for a query
    def parse_search_api_response(self, response):
        json_response = json.loads(response.body_as_unicode())
        for new in json_response["posts"]:
            if new: 
                yield response.follow(new["url"], headers=self.get_headers(), callback=self.parse_new)

    def parse_new(self,response):
        if response.status != 200:
            yield {
                'status': 0,
                'response_code': response.status
            }
        else:
            post = response.css('div.post-page__item')

            if post:
                post = post[0]
                # #obtain attributes of the new
                id = int(post.xpath('//div[contains(@class, "post-page__article")]/article[contains\
                    (@class, "post__article")]/@id').get().split('-')[1])
                author = post.css('div.post-page__article article.post__article div.post-meta\
                    div.post-meta__author a.post-meta__author-link div::text').get().strip()
                datetime = post.css('div.post-page__article article.post__article div.post-meta div.post-meta__publish-date time::attr(datetime)').get().strip()              
                datetime = dt.strptime(datetime, DATETIME_FORMAT_INPUT)
                title = post.css('div.post-page__article article.post__article h1.post__title::text').get().strip()
                description = post.css('div.post-page__article article.post__article p.post__lead::text').get().strip()

                #obtain the content of the new
                content = []
                paragraphs = post.xpath('//div[contains(@class, "post-page__article")]/article[contains\
                    (@class, "post__article")]/div[contains(@class, "post__content-wrapper")]/\
                    div[contains(@class, "post-content")]/*[self::p or self::h3 or self::blockquote]')

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

                # #obtain the tags related to the new
                tags = [tag.strip() for tag in post.css('div.tags-list ul li a::text').getall()]


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
            else:
                yield {
                    'status': 3,
                    'response_code': response.status
                }