from HTMLParser import HTMLParser
from google.appengine.api import urlfetch

class BlognoneNewsImage:
    entryID = 0
    imageLink = ''

class Image_Tag_Spider(HTMLParser):
    
    
    def __init__(self, url):
        HTMLParser.__init__(self)
        
        req = urlfetch.fetch( url )
        self.aLink = ''
        self.entryID = ''
        self.Thumbnails = []
        #self.feed(req.content)
        self.feed(unicode(req.content, 'utf-8'))

    def handle_starttag(self, tag, attrs):
        if tag == 'a' and attrs[0][1].find('news/') != -1:
            #print "a link => %s" % attrs[0][1]
            self.aLink = attrs[0][1]
            self.entryID = self.aLink.split('/news/')[1]
        if tag == 'img' and attrs[0][1].find('news-thumbnail') != -1:
            #print "Found link => %s" % self.aLink
            #print self.entryID
            #print "Found image => %s" % attrs[0][1]
            #print ''
            tmpData = BlognoneNewsImage()
            tmpData.entryID = long(self.entryID)
            tmpData.imageLink = attrs[0][1]
            self.Thumbnails.append(tmpData)
            
            
class Comment_Spider(HTMLParser):
    
    
    # fetching all comments in an entry
    # Work Flow
    
    # 1. Check start tag of div class comment-content [handle_starttag]
    # 2. Get comment from data in p tag [handle_data]
    # 3. end tag of div class comment-content [handle_endtag]
    # loop to do it again in step 1
    
    def __init__(self, url):
        HTMLParser.__init__(self)
        
        req = urlfetch.fetch( url )
        self.Comments = []
        self.comment_id = -1
        self.comment_data = []
        self.div_stage = ''
        #self.feed(req.content)
        self.feed(unicode(req.content, 'utf-8'))

    def handle_starttag(self, tag, attrs):
        #find root div of all comments
        
        #if tag == 'div':
        #    if len(attrs) == 1:
        #        self.Comments.append(attrs[0][1])
        #    elif len(attrs) == 2:
        #        self.Comments.append(attrs[1][1])
        
        if tag == 'div' and len(attrs) == 2 and attrs[1][1].strip() == 'comment clear-block':
            # content in attrs
            # row 0 -- [id][cid-261772]
            # row 1 -- [class][comment clear-block]
            #get comment id 
            if self.div_stage == '':
                self.comment_id = attrs[0][1]
                self.div_stage = 'comment clear-block'
            
        if tag == 'div' and len(attrs) == 1 and attrs[0][1].strip() == 'comment-info':
            if self.div_stage == 'comment clear-block':
                self.div_stage = 'comment-info'
        
        if tag == 'div' and len(attrs) == 1 and attrs[0][1].strip() == 'user_badges':
            if self.div_stage == 'comment-info':
                self.div_stage = 'user_badges'
            
        if tag == 'div' and len(attrs) == 1 and attrs[0][1].strip() == 'comment-body':
            if self.div_stage == 'comment clear-block':
                self.div_stage = 'comment-body'
            
        if tag == 'div' and len(attrs) == 1 and attrs[0][1].strip() == 'comment-user-picture':
            if self.div_stage == 'comment-body':
                self.div_stage = 'comment-user-picture'
            
        if tag == 'div' and len(attrs) == 1 and attrs[0][1].strip() == 'picture':
            if self.div_stage == 'comment-user-picture':
                self.div_stage = 'picture'
            
        if tag == 'div' and len(attrs) == 1 and attrs[0][1].strip() == 'comment-content':
            if self.div_stage == 'comment-body':
                self.div_stage = 'comment-content'
            
        if tag == 'div' and len(attrs) == 1 and attrs[0][1].strip() == 'comment-links':
            if self.div_stage == 'comment-body':
                self.div_stage = 'comment-links'
            
        #if self.div_stage <> '':
        #    self.Comments.append(self.div_stage)
    
    def handle_endtag(self, tag):
        if tag == 'div':
            
            if self.div_stage == 'comment-links':
                self.div_stage = 'comment-body'
                
            elif self.div_stage == 'comment-content':
                self.div_stage = 'comment-body'
                
            elif self.div_stage == 'picture':
                self.div_stage = 'comment-user-picture'
                
            elif self.div_stage == 'comment-user-picture':
                self.div_stage = 'comment-body'
                
            elif self.div_stage == 'comment-body':
                self.div_stage = 'comment clear-block'
                
            elif self.div_stage == 'user_badges':
                self.div_stage = 'comment-info'
                
            elif self.div_stage == 'comment-info':
                self.div_stage = 'comment clear-block'
                
            elif self.div_stage == 'comment clear-block':
                #self.comment_data = self.comment_data + ' ' + self.comment_id
                #self.Comments.append(self.comment_id)
                #self.comment_data = self.comment_data + ' <span style="color:#999999;">' + self.comment_id + '</span>'
                self.comment_data.append(self.comment_id)
                self.Comments.append(self.comment_data)
                self.comment_data = []
                self.comment_id = -1
                self.div_stage = ''
            
        #self.comment_id = -1
        
    def handle_data(self, data):
        if data.strip() <> '':
            self.comment_data.append(data)
        #if self.div_stage == 'comment-content' and data.strip() <> '':
        #    self.comment_data.append(data)
                
        #if self.div_stage == 'comment-info' and data.find('By:') <> -1:
        #    self.comment_data = data + '\n<br>'

