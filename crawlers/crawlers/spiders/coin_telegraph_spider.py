import scrapy


class CoinTelegraphSpider(scrapy.Spider):
    name = "coin_telegraph"
    headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:74.0) Gecko/20100101 \
            Firefox/74.0'
    }
    def start_requests(self):
        urls = ['https://cointelegraph.com/tags/bitcoin']
        # urls = [
        #     'https://cointelegraph.com/tags/bitcoin',
        #     'https://cointelegraph.com/tags/ripple',
        #     'https://cointelegraph.com/tags/ethereum',
        #     'https://cointelegraph.com/tags/litecoin'
        # ]

        for url in urls:
            yield scrapy.Request(url=url, headers=self.headers, callback=self.parse)

    def parse(self, response):
        #get the list of links we need for the news
        news_list = response.css('li.post-preview-list-inline__item')
        for news_item in news_list:
            link = news_item.css('div.post-preview-item-inline article.post-preview-item-inline__article \
                                a::attr(href)').get().strip()
            title = news_item.css('div.post-preview-item-inline article.post-preview-item-inline__article \
                div.post-preview-item-inline__content header.post-preview-item-inline__header \
                div.post-preview-item-inline__title-wrp a span::text').get().strip()
            print(link,title)
            #follow the link to get the actual content of the new
            if link is not None:
                yield response.follow(link, headers=self.headers, callback=self.parse_new)

    def parse_new(self,response):
        yield response.status