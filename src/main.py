#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import feedparser
import datetime
import urllib
urllib.getproxies_macosx_sysconf = lambda: {}
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from google.appengine.ext import db

from google.appengine.api import quota

from django.utils import simplejson as json

from blognone_spider import Image_Tag_Spider
from blognone_spider import Comment_Spider

# blognone entry
class Blognone_News(db.Model):
    entryID = db.IntegerProperty()
    thumbnailURL = db.LinkProperty()
    title = db.StringProperty()
    description = db.TextProperty()
    url = db.StringProperty()
    author = db.StringProperty()
    date = db.DateTimeProperty()
    added = db.DateTimeProperty(auto_now_add=True)
    

class MainHandler(webapp.RequestHandler):
    def get(self):
        start = quota.get_request_cpu_usage()
        self.response.out.write('Welcome')
        
        end = quota.get_request_cpu_usage()
        logging.info("Main() cost %d megacycles." % (start - end))
        
class Fetch(webapp.RequestHandler):
    def get(self):
        start = quota.get_request_cpu_usage()
        # Fetch feed from URL
        feed_url = "http://www.blognone.com/atom.xml"
        feedinput = urlfetch.fetch( feed_url )
        d = feedparser.parse( feedinput.content )
        if d.bozo == 1:
            raise Exception("Can not parse given URL.")
                
        # Fetch Tag Image for News  
        thumbnailSpider = Image_Tag_Spider('http://www.blognone.com/')
            
        # make array from feed
        feeds = []
        for entry in d['entries']:
            entryID = long(entry.links[0].href.split('/news/')[1])
            title = entry.title
            description = entry.description
            url = entry.links[0].href
            author = entry.author
            date = entry.updated
            date2 = str(entry.date_parsed.tm_mday) + ' ' + str(entry.date_parsed.tm_mon) + ' ' + str(entry.date_parsed.tm_year)
            
            feed = { "title": title, "description": description, "url": url, "author": author, "date": date, "date2": date2 }
            feeds.append( feed )
            
            # put to blognone entry
            # convert the given time format to datetime
            posted_datetime = datetime.datetime(
                entry['updated_parsed'][0],
                entry['updated_parsed'][1],
                entry['updated_parsed'][2],
                entry['updated_parsed'][3],
                entry['updated_parsed'][4],
                entry['updated_parsed'][5],
                entry['updated_parsed'][6],
            )
        
            # Insert if not exist
            entries2 = db.GqlQuery("SELECT * FROM Blognone_News WHERE url = :where_url ORDER BY date DESC", where_url = url)
            
            if entries2.count() == 0:
                news = Blognone_News();
                news.entryID = entryID
                news.title = title
                news.description = description
                news.url = url
                news.author = author
                news.date = posted_datetime
                
                # assign tag image to news
                #for newsThumbnail in thumbnailSpider.Thumbnails:
                #    if newsThumbnail.entryID == entryID:
                #        news.thumbnailURL = newsThumbnail.imageLink
                
                news.put()
                
        # Update missing thumbnail        
        for newsThumbnail in thumbnailSpider.Thumbnails:
            #self.response.out.write(newsThumbnail.imageLink)
            #self.response.out.write(newsThumbnail.entryID + '<br>')
            entries3 = db.GqlQuery("SELECT * FROM Blognone_News WHERE entryID = :entryID", entryID = newsThumbnail.entryID)
            for entry in entries3:
                if entry.thumbnailURL == None:
                    entry.thumbnailURL = newsThumbnail.imageLink
                    entry.put()
                    

        # display feed by template    
        #template_values = {
        #    'feeds': feeds
        #}
        
        #self.response.out.write(d.entries[0])
        #path = os.path.join(os.path.dirname(__file__), 'index.html')
        #self.response.out.write(template.render(path, template_values))
        
        end = quota.get_request_cpu_usage()
        logging.info("Fetch() cost %d megacycles." % (start - end))
     
# Fetching comments of an entry
class Fetch_Comment(webapp.RequestHandler):
    def get(self):
        
        # Read comments from an entry  
        CommentSpider = Comment_Spider("http://www.blognone.com/news/21984")
        #self.response.out.write(CommentSpider.Comments)
        
        template_values = {
            'comments': CommentSpider.Comments
            }
        
        path = os.path.join(os.path.dirname(__file__), 'browse_comment.html')
        self.response.out.write(template.render(path, template_values))
        #for newsThumbnail in CommentSpider.Thumbnails:
        #    self.response.out.write(newsThumbnail)
        
        
class Browse(webapp.RequestHandler):
    def get(self):
        start = quota.get_request_cpu_usage()
        # Getting blognone news from datastore
        entries = db.GqlQuery("SELECT * FROM Blognone_News ORDER BY date DESC")

        template_values = {
            'entries': entries
            }

        path = os.path.join(os.path.dirname(__file__), 'browse.html')
        self.response.out.write(template.render(path, template_values))
        
        end = quota.get_request_cpu_usage()
        logging.info("Browse() cost %d megacycles." % (start - end))
        
class Browse_Json(webapp.RequestHandler):
    def get(self):
        start = quota.get_request_cpu_usage()
        # Getting and converting to json from blognone news from datastore
        entries = db.GqlQuery("SELECT * FROM Blognone_News ORDER BY date DESC")
        
        all_news = []
        for entry in entries:
            temp = {
                'id': entry.key().id(),
                'entry_id': entry.entryID,
                'title': entry.title,
                'short_description': entry.description[0:34],
                #'description': entry.description,
                'url': entry.url,
                'thumbnailURL': entry.thumbnailURL,
                'author': entry.author
                }
            all_news.append(temp)
        
        self.response.out.write(json.dumps(all_news))
        
        end = quota.get_request_cpu_usage()
        logging.info("Browse_Json() cost %d megacycles." % (start - end))
        
class Browse_Json_Since_Last_Fetched(webapp.RequestHandler):
    def get(self):
        start = quota.get_request_cpu_usage()
        # Getting since last fetched and converting to json from blognone news from datastore 
        last_fetched_id = int(self.request.get('last_fetched_id'))
        if last_fetched_id == -1:
            entries = Blognone_News.all()
        else:
            #last_entry = Blognone_News.get_by_id(last_fetched_id)
            entries = Blognone_News().all()
            entries.filter('entryID > ', last_fetched_id)
        
        
        all_news = []
        for entry in entries:
            temp = {
                'id': entry.key().id(),
                'entry_id': entry.entryID,
                'title': entry.title,
                'short_description': entry.description[0:34],
                #'description': entry.description,
                'url': entry.url,
                'thumbnailURL': entry.thumbnailURL,
                'author': entry.author
                }
            all_news.append(temp)
        
        self.response.out.write(json.dumps(all_news))
        
        end = quota.get_request_cpu_usage()
        logging.info("Browse_Json() cost %d megacycles." % (start - end))
        
class Get_Entry(webapp.RequestHandler):
    def get(self):
        start = quota.get_request_cpu_usage()
        # 
        entry_id = int(self.request.get('entry_id'))
        entries = Blognone_News().all()
        entries.filter('entryID == ', entry_id)
        
        # get comment
        #all_comment = '<table border="1"><tr><td> ' + 'http://www.blognone.com/news/' + str(entry_id) + '</td></tr>\n'
        CommentSpider = Comment_Spider('http://www.blognone.com/news/' + str(entry_id))
        #for comment in CommentSpider.Comments:
        #    all_comment = all_comment + '<tr><td>' + comment + '</td></tr>\n'
        #all_comment = all_comment + '</table>'
        
        entry = entries[0]
        entry_json = {
            'id': entry.key().id(),
            'title': entry.title,
            'description': entry.description,
            'comment': CommentSpider.Comments,
            'url': entry.url,
            'author': entry.author
            } 
        
        self.response.out.write(json.dumps(entry_json))
        
        end = quota.get_request_cpu_usage()
        logging.info("Get_Entry() cost %d megacycles." % (start - end))
        
        
class Delete(webapp.RequestHandler):
    def get(self):
        start = quota.get_request_cpu_usage()
        # Deleting all of blognone news
        entries = db.GqlQuery("SELECT * FROM Blognone_News ORDER BY date DESC")
        
        for entry in entries:
            self.response.out.write('Deleting ' + entry.title + '<br />')
            entry.delete()
            
        end = quota.get_request_cpu_usage()
        logging.info("Delete() cost %d megacycles." % (start - end))
        
        
class Browse_Thumbnail(webapp.RequestHandler):
    def get(self):
        # Fetch Tag Image for News  
        thumbnailSpider = Image_Tag_Spider('http://www.blognone.com/')
        for newsThumbnail in thumbnailSpider.Thumbnails:
            
            self.response.out.write(newsThumbnail.entryID + ' ' + newsThumbnail.imageLink + '<br>')

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/fetch', Fetch),
                                          ('/fetch_comment', Fetch_Comment),
                                          ('/browse', Browse),
                                          ('/get_entry', Get_Entry),
                                          ('/browse_json', Browse_Json),
                                          ('/browse_json_since_last_fetched', Browse_Json_Since_Last_Fetched),
                                          ('/browse_thumbnail', Browse_Thumbnail),
                                          ('/delete', Delete)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
