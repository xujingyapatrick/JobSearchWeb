# -*- coding:utf-8 -*-  
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
import datetime
import pymongo
from pymongo import MongoClient
import dateutil.relativedelta
from datetime import timedelta, date



def getDataAndSend():
    today , old = getLatestItems()
    send(today, old)

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield end_date - timedelta(n+1)

def getLatestItems():
    client = MongoClient('localhost', 27017)
    db = client.indeed.jobs
    todayData = db.find({'date': str(datetime.date.today())}).sort([('date',1)]).limit(1000)
    old = []
    today = datetime.date.today()
    start_day = today - dateutil.relativedelta.relativedelta(days=10)
    for single_date in daterange(start_day, today):
        jobData = db.find({u'date':  str(single_date)  }).sort([('date',1)]).limit(1000)
        count = jobData.count()
        if count == 0:
            continue
        jobPack = {u'date' : str(single_date), 'jobData': jobData}
        old.append(jobPack)
    return todayData,old

def send(today, old):
    # me == my email address
    # you == recipient's email address
    me = ""
    you = []
    # you=["jxu@itu.edu"]
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = u"NEW!! Today's Indeed Entry Level Software Posts" + str(datetime.date.today())
    msg['From'] = me
    msg['To'] = ", ".join(you)
    
    print "hello"
    print today , old

    # Create the body of the message (a plain-text and an HTML version).
    html = """\
    <ul class="list-group">
          <h2> Today's Entry level positions: </h2>
      {% for n in today %} 
      <li class="list-group-item"><a href={{n.url}}><font size="2" color="red">{{n.company}}</font> <font size="2" color="blue">{{n.address}}</font> <font size="2" color="green">{{n.title}}</font></a></li>
      {% endfor %}
          <h4> Previous: </h4>
      {% for pack in old %}
          <h4> {{ pack.date }} </h4>
          {% for item in pack.jobData %}
              <li class="list-group-item"><a href={{item.url}}><font size="2" color="black">{{item.company}}</font><font size="2" color="orange">{{item.address}}</font><font size="2" color="orange">{{item.title}}</font></a></li>
              {% endfor %}
      {% endfor %}
    </ul>
    """

    t = Template(html)
    html = t.render(date = str(datetime.date.today()), today = today, old = old)
    part2 = MIMEText(html.encode('utf-8'), 'html',_charset='utf-8')

    msg.attach(part2)
    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)

    mail.ehlo()

    mail.starttls()

    mail.login("xxx@gmail.com","password")
    mail.sendmail(me, you, msg.as_string())
    mail.quit()


getDataAndSend()
 