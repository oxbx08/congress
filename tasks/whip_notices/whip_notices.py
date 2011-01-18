import feedparser
import urllib2
from BeautifulSoup import BeautifulSoup, SoupStrainer
import re
import datetime, time

PREFIX = 'http://www.democraticwhip.gov/'

def run(db):
    total_count = 0
    total_count += house_dem(db, 'daily', "%srss/32/all" % PREFIX)
    total_count += house_dem(db, 'nightly', "%srss/34/all" % PREFIX)
    total_count += house_dem(db, 'weekly', "%srss/31/all" % PREFIX)
    
    # broken in the transition
    # total_count += house_rep(db)
    
    db.success("Updated or created %s whip notices" % total_count)


def house_dem(db, notice_type, source):
    count = 0
    doc = feedparser.parse(source)
    items = doc['items']
    for item in items:
        url = '%s%s' % (PREFIX, item.link.replace('&amp;', '&').replace(PREFIX, ''))
        
        posted_at = datetime.datetime(*item.updated_parsed[:6])
        session = current_session(posted_at.year)
      
        notice = db.get_or_initialize("whip_notices", {
          "chamber": 'house', 
          "posted_at": posted_at, 
          "party": 'D', 
          "notice_type": notice_type
        })
        
        notice['url'] = url
        notice['session'] = session
        
        db['whip_notices'].save(notice)
        
        count += 1
    
    return count


def house_rep(db):
    try:
        page = urllib2.urlopen("http://republicanwhip.house.gov/floor/")
    except:
        db.warning("Couldn't load Republican Whip house floor page, skipping")
        
    else:
        soup = BeautifulSoup(page)
        titles = soup.findAll('span', {'class':'h2a'})
        
        daily_title = 'The Whipping Post - '
        weekly_title = 'The Whip Notice - Week of '
        
        count = 0
        
        for title in titles:
            daily_re = re.compile(daily_title)
            weekly_re = re.compile(weekly_title)
            title_str = title.contents[0].strip()
            
            if weekly_re.match(title_str):
                weekly_date_str = title_str.replace(weekly_title, '').strip()
                weekly_date = datetime.datetime(*time.strptime(weekly_date_str, "%m/%d/%y")[0:6])
                session = current_session(weekly_date.year)
                weekly_url = "http://republicanwhip.house.gov/floor/%s.pdf" % single_digify(weekly_date.strftime("%m-%d-%y"))
                
                notice = db.get_or_initialize("whip_notices", {
                  'chamber': "house", 
                  'posted_at': weekly_date, 
                  'party': "R", 
                  'notice_type': "weekly"
                })
                
                notice['url'] = weekly_url
                notice['session'] = session
                
                db['whip_notices'].save(notice)
                
                count += 1
                
        return count
      
          # Daily PDFs appear to have been removed
          
          #elif daily_re.match(title_str):
              #daily_date_str = title_str.replace(daily_title, '').strip()
              #daily_date = datetime.datetime(*time.strptime(daily_date_str, "%m/%d/%y")[0:6])
              #daily_url = "http://republicanwhip.house.gov/floor/%s.pdf" % single_digify(daily_date.strftime("%m-%d-%y"))
              
              #session = current_session(daily_date.year)
              
              #notice = db.get_or_initialize("whip_notices", {
                #'chamber': "house", 
                #'posted_at': daily_date, 
                #'party': "R", 
                #'notice_type': "daily"
              #})
              
              #notice ['url'] = daily_url
              #notice['session'] = session
              #db['whip_notices'].save(notice)
      


def single_digify(date_str):
    m_str = date_str.split('-')[0].lstrip('0')
    d_str = date_str.split('-')[1].lstrip('0')
    y_str = date_str.split('-')[2]
    return "%s-%s-%s" % (m_str, d_str, y_str)     

#handy string cleaning functions found at http://love-python.blogspot.com/2008/07/strip-html-tags-using-python.html
def remove_extra_spaces(data):
    p = re.compile(r'\s+')
    return p.sub(' ', data)

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def current_session(year=None):
  if not year:
    year = datetime.datetime.now().year
  return ((year + 1) / 2) - 894