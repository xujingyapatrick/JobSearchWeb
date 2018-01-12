import scrapy
from bs4 import BeautifulSoup
import re
import pymongo
from pymongo import MongoClient
import io
import datetime
import time


class IndeedSpider(scrapy.Spider):
    name = "indeed"
    client = MongoClient('localhost', 27017)
    db = client.indeed.fulltime
    count = 0
    chunk = ""
    def clean_html(self,html):
	    """
	    Copied from NLTK package.
	    Remove HTML markup from the given string.

	    :param html: the HTML string to be cleaned
	    :type html: str
	    :rtype: str
	    """

	    # First we remove inline JavaScript/CSS:
	    cleaned = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html.strip())
	    # Then we remove html comments. This has to be done before removing regular
	    # tags since comments can contain '>' characters.
	    cleaned = re.sub(r"(?s)<!--(.*?)-->[\n]?", "", cleaned)
	    # Next we can remove the remaining tags:
	    cleaned = re.sub(r"(?s)<.*?>", " ", cleaned)
	    # Finally, we deal with whitespace
	    cleaned = re.sub(r"&nbsp;", " ", cleaned)
	    cleaned = re.sub(r"  ", " ", cleaned)
	    cleaned = re.sub(r"  ", " ", cleaned)
	    return cleaned.strip()

    def start_requests(self):
        urls = [
            "https://www.indeed.com/jobs?q=%22full+stack+developer%22+OR+%22full+stack+engineer%22+OR+%22cloud+developer%22+OR+%22cloud+engineer%22+OR+%22software+developer%22+OR+%22software+engineer%22+OR+%22application+engineer%22+OR+%22application+developer%22+NOT+%22senior%22+NOT+%223+years%22+NOT+%225+years%22+NOT+%22volunteer%22+NOT+%22Sr.%22+NOT+%22ios%22+NOT+%22.NET%22+NOT+%223%2B%22+NOT+%225%2B%22+NOT+%224%2B%22+NOT+%22administrator%22+NOT+%22UI%22+NOT+%22sales+engineer%22&l=94002&explvl=entry_level&radius=50&sort=date",
            "https://www.indeed.com/jobs?q=%22full+stack+developer%22+OR+%22full+stack+engineer%22+OR+%22cloud+developer%22+OR+%22cloud+engineer%22+OR+%22software+developer%22+OR+%22software+engineer%22+OR+%22application+engineer%22+OR+%22application+developer%22+NOT+%22senior%22+NOT+%223+years%22+NOT+%225+years%22+NOT+%22volunteer%22+NOT+%22Sr.%22+NOT+%22ios%22+NOT+%22.NET%22+NOT+%223%2B%22+NOT+%225%2B%22+NOT+%224%2B%22+NOT+%22administrator%22+NOT+%22UI%22+NOT+%22sales+engineer%22&l=98139&radius=50&explvl=entry_level&sort=date",
            "https://www.indeed.com/jobs?q=%22full+stack+developer%22+OR+%22full+stack+engineer%22+OR+%22cloud+developer%22+OR+%22back+end%22+OR+%22backend%22+OR+%22new+grad+software%22+OR+%22software+developer%22+OR+%22software+engineer%22+OR+%22application+engineer%22+OR+%22application+developer%22+NOT+%22senior%22+NOT+%223+years%22+NOT+%225+years%22+NOT+%22volunteer%22+NOT+%22Sr.%22+NOT+%22ios%22+NOT+%22.NET%22+NOT+%223%2B%22+NOT+%225%2B%22+NOT+%224%2B%22+NOT+%22administrator%22+NOT+%22UI%22+NOT+%22sales+engineer%22&l=94002&radius=50&sort=date",
            "https://www.indeed.com/jobs?q=%22full+stack+developer%22+OR+%22full+stack+engineer%22+OR+%22cloud+developer%22+OR+%22back+end%22+OR+%22backend%22+OR+%22new+grad+software%22+OR+%22software+developer%22+OR+%22software+engineer%22+OR+%22application+engineer%22+OR+%22application+developer%22+NOT+%22senior%22+NOT+%223+years%22+NOT+%225+years%22+NOT+%22volunteer%22+NOT+%22Sr.%22+NOT+%22ios%22+NOT+%22.NET%22+NOT+%223%2B%22+NOT+%225%2B%22+NOT+%224%2B%22+NOT+%22administrator%22+NOT+%22UI%22+NOT+%22sales+engineer%22&l=98139&radius=50&sort=date",

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parseMore(self, response):
        html = response.css('body').extract_first()
        html = self.clean_html(html)
        soup = BeautifulSoup(html)
        db = self.client.indeed
        self.chunk = self.chunk + soup.get_text()
        jobItem = {"title" : response.meta['title'], 
               "company" : response.meta['company'],
               "detailUrl" : response.meta['detailUrl'],
               "desp" : soup.get_text()}
        jobId = db.jobs.insert_one(jobItem).inserted_id
        self.count = self.count + 1
        print self.count



    def parse(self, response):
        time.sleep(1)
        jobResults = response.css('div.row.result')
        for jobResult in  jobResults:
            title = jobResult.css('a.turnstileLink::attr(title)').extract_first()
            if not title:
                title = "unknown"

            company = jobResult.css('span.company')[0].css('a::text').extract_first()
            if not company or not company.strip():
                company = jobResult.css('span.company')[0].css('span::text').extract_first()
            if not company or not company.strip():
                company = jobResult.css('span.company')[0].css('span.a::text').extract_first()
            if not company or not company.strip():
                company = "unknown"
            location = jobResult.css('span.location').css('span::text').extract_first()    
            if not location or not location.strip():
                location = "unknown"
            location = location.strip()
            summary = jobResult.css('span.summary::text').extract_first()    
            if not summary:
                summary = "unknown"
            summary = summary.strip()
            if len(summary)>60:
                summary = summary[0:60]
            date = str(datetime.date.today())

            detailUrl = jobResult.css('a.turnstileLink').css('a::attr(href)').extract_first()
            
            if title:
                title = title.strip()
            if company:
                company = company.strip()
            if detailUrl:
                detailUrl = detailUrl.strip()
            if detailUrl.startswith('/'):
                detailUrl = "https://www.indeed.com" + detailUrl
            hashCode = hash(company+title+location+summary)
            item={}
            item['title']=title
            item['_id'] = hashCode
            item['date'] = date
            item['url']=detailUrl
            item['company']=company
            item['address']=location
            if not self.exists(item, self.db):  
                self.db.insert_one(item)
            
        next_page = response.css('div.pagination').css('a')[-1].css('a::attr(href)').extract_first()
        
        
        # if self.count > 11000:
        #     filename = 'train_data.txt'
        #     #print(self.chunk)
        #     with io.open(filename, 'w', encoding='utf-8') as file:
        #         file.write(self.chunk) 
        #         self.log('Saved file %s' % filename)
        #     return 
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            print "next none, bye bye"

    def exists(self,item,collection):
        return collection.find_one({'_id' : item['_id']}) != None
