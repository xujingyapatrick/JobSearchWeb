from scrapy.selector import Selector
from bs4 import BeautifulSoup
import re
import pymongo
from pymongo import MongoClient
import io
from selenium import webdriver
import time, random
from selenium.webdriver.support.ui import Select
from dbhelper import DBhelper
import datetime
from selenium.common.exceptions import NoSuchElementException
import mailsender
from pyvirtualdisplay import Display


class LinkedinSpider(object):
    name = "linkedin"
    dbhelper=DBhelper()
    start_urls=["https://www.linkedin.com"]
    crawled_count=0

    def waitForLoading(self):
        time.sleep(5+random.randint(3,9))
        return
    def findNewJobs(self):
        display = Display(visible=0, size=(1300, 1500))
        display.start()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        driver = webdriver.Chrome('/home/ubuntu/tmptransfer/chromedriver',chrome_options=chrome_options)
        driver.set_window_size(1300, 1500)
        # driver.execute_script("document.body.style.zoom='70%'")
        #login account
        driver.get(self.start_urls[0])
        self.waitForLoading()
        driver.find_element_by_name(u"session_key").clear()
        driver.find_element_by_name(u"session_key").send_keys(u"email...")
        driver.find_element_by_name(u"session_password").clear()
        driver.find_element_by_name(u"session_password").send_keys(u"password")
        driver.find_element_by_css_selector("input#login-submit.login.submit-button").click()
        self.waitForLoading()
        #go to search and set software, entry level, computer... i.e. set up search and search
        driver.find_element_by_css_selector(u"button.nav-search-button").click()
        self.waitForLoading()
        
        lilist = driver.find_elements_by_class_name(u"sub-nav-item")
        lilist[2].find_element_by_tag_name("button").click()
        self.waitForLoading()
        
        inputDiv=driver.find_element_by_css_selector("div.jobs-search-box__input.jobs-search-box__input--keyword")
        inputDivs = inputDiv.find_elements_by_tag_name("input")
        inputDivs[1].clear()
        inputDivs[1].send_keys("(full stack developer OR full stack engineer OR cloud developer OR cloud engineer OR software developer OR software engineer OR application engineer OR application developer)")
        driver.find_element_by_css_selector("button.jobs-search-box__submit-button.button-primary-large").click()
        self.waitForLoading()
        select=Select(driver.find_element_by_id("sort-dropdown-select"))
        select.select_by_visible_text("Post date")
        self.waitForLoading()
        
        # driver.execute_script("window.scrollTo(0, 600);")

        # time.sleep(1)
        buttons=driver.find_elements_by_css_selector("button.search-s-facet__name-wrap")
        buttons[2].click()
        # time.sleep(1)
        forms=driver.find_elements_by_css_selector("form.search-s-facet-form")
        boxs=forms[2].find_elements_by_css_selector("li.search-s-facet-value")
        boxs[0].click()
        self.waitForLoading()

        page_count=0
        while self.crawled_count<25 and page_count<25:
            page_count=page_count+1
            body=driver.find_element_by_tag_name("body")
            print(body.size)
            height=body.size['height']/20
            for h in range(1,height):
                script="window.scrollTo(0, "+str(h*20)+");"
                driver.execute_script(script)
                time.sleep(0.1)
            body=driver.find_element_by_tag_name("body")
            #print(body.size)
            height=body.size['height']/20
            
            for h in range(1,height):
                script="window.scrollTo(0, "+str((height-h)*20)+");"
                driver.execute_script(script)
                time.sleep(0.05)
            body=driver.find_element_by_tag_name("body")
            # print(body.size)
            height=body.size['height']/20
            
            for h in range(1,height):
                script="window.scrollTo(0, "+str(h*20)+");"
                driver.execute_script(script)
                time.sleep(0.05)
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # self.waitForLoading()
            source=driver.page_source.encode('utf8')
            # source=driver.find_element_by_tag_name("body").text
            self.crawled_count=0
            self.extract_items_scrapy(source)
            # find_element_by_css_selector("ul.card-list.card-list--column.jobs-search-results__list")
            # jobs=ul.find_elements_by_tag_name("a")
            # crawled_count= self.extract_items(jobs,crawled_count)
            try:
                next=driver.find_element_by_css_selector("button.next")
            except :
                print("find next page button ERROR!!!")
                break
            next.click()
            self.waitForLoading()
        driver.close()
        display.stop()
        print("entry level positions crawl end! BYE!")

    # get new jobs and send email
    def sendmail(self):
        today , old = self.dbhelper.getLatestItems()
        mailsender.send(today = today, old = old)
        return

    def extract_items_scrapy(self,source):
        targetLocations=['CA','NY','WA','Seattle']
        selector=Selector(text=source, type="html")
        db=self.dbhelper.client.linkedinentry
        # filename="page.html"
        # with open(filename,'wb') as f:
        #     f.write(source)
        ul=selector.css('div.jobs-search-results').xpath('./ul')
        divlist=ul.xpath("./div/div[2]/div[1]/div[1]")
        print("len(divlist)="+str(len(divlist)))

        for div in divlist:
            url=div.xpath("./a/@href").extract()
            if len(url)==1:
                url=url[0].encode('utf8')
                url=self.start_urls[0]+url[:(url.find('/',14))]
            else:
                url=self.start_urls[0]
            
            companie=div.css("h4.job-card__company-name::text").extract()
            if len(companie)!=1:
                companie=[u"unknown"]
            address=div.css("h5.job-card__location::text").extract()
            if len(address)!=2:
                address=[u"unknown"]
            else:
                address[0]=address[1].strip(' ').strip('\n').strip(' ')
            dropThis=True
            for loc in targetLocations:
                if address[0].find(loc)!=-1:
                    dropThis=False
                    break
            if dropThis==True:
                continue
                
            title1=div.css("span.truncate-multiline--last-line-wrapper").xpath("./span/text()").extract()
            if len(title1)==1:
                title1=title1[0]
            else:
                title1=u'unknown'
            #title2=div.css("div.truncate-multiline--truncation-target").xpath("./span/text()").extract()
            #if len(title2)==1:
            #    title2=title2[0]
            #else:
            #    title2=u'unknown'
            title=title1
            
            
            hashCode=hash(companie[0]+title + url)
            date=str(datetime.date.today())
            item={}
            item['title']=title
            item['_id'] = hashCode
            item['date'] = date
            item['url']=url
            item['company']=companie[0]+": "
            item['address']=address[0]
    # print("Job title:"+item['title']+"  Link:"+item['url'])
            item1={}
            item1['title']=title
            item1['_id'] = hash(companie[0]+title+address[0])
            item1['date'] = date
            item1['url']=url
            item1['company']=companie[0]+": "
            item1['address']=address[0]

            if self.exists(item1, db.repo):  
                self.crawled_count=self.crawled_count+1
                db.repo.update({'_id' : item1['_id']},{'$set':{'url':item1['url']}})
            else:
                self.dbhelper.insert_one(item1)
        # print("Job title:"+item['title']+"  Link:"+item['url'])
        print("crawled_count= "+str(self.crawled_count))
        return

    def exists(self,item,collection):
        return collection.find_one({'_id' : item['_id']}) != None
