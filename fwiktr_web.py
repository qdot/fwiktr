import time
import os
import sys
import twitter
import urllib
import math
import random
import uuid
import ConfigParser
import pycurl
import cgi
from flickrapi import FlickrAPI
from nltk import tag, corpora, tokenize

xml_block = '''<?xml version='1.0' standalone='yes'?>
<fwiktr>
  <post flickr_farm='%(flickr_farm)s' flickr_server='%(flickr_server)s' flickr_photoid='%(flickr_photoid)s' flickr_ownerid='%(flickr_ownerid)s' flickr_title='%(flickr_title)s' flickr_secret='%(flickr_secret)s' post_source='%(post_source)s' chain_mechanism='%(chain_mechanism)s' selection_mechanism='%(selection_mechanism)s' flickr_total='%(flickr_total)s' post_date='%(post date)s'>
    <text>%(post_text)s</text>
    <tags>%(post_tags)s</tags>
    <pos_output>%(post_pos_output)s</pos_output>
    %(twitter_info_block)s
  </post>
</fwiktr>
'''

twitter_info_block = '''
<twitter>
    <twitter_post_id>%(twitter_post_id)s<twitter_post_id>
    <twitter_author_id>%(twitter_author_id)s</twitter_author_id>
    <twitter_author_name>%(twitter_author_name)s</twitter_author_name>
    <twitter_location>%(twitter_location)s</twitter_location>
</twitter>
'''
class Fwiktr:
    def __init__(self):
        self._config = None
        self._curl = pycurl.Curl()
#        self._curl.global_init(pycurl.GLOBAL_DEFAULT)

        self.SetupFlickr()
        self.SetupTwitter()

    def _GetOption(self, option):
        try:
            return self._GetConfig().get('Fwiktr', option)
        except:
            return None

    def _GetConfig(self):
        if not self._config:
            self._config = ConfigParser.ConfigParser()
            self._config.read(os.path.expanduser('~/.fwiktrrc'))        
        return self._config

    def SetupFlickr(self):
        self.fapi = FlickrAPI(self._GetOption('flickr_api_key'), self._GetOption('flickr_api_secret'))

    def SetupTwitter(self):
        self.tapi = twitter.Api()        

    def RunPOSTagger(self):
        twitter_messages = self.tapi.GetPublicTimeline()
        for message in twitter_messages:
            try:
                self.fwiktr_info = {'chain_mechanism':1, 'selection_mechanism':1, 'post_source':1, 'post_date':message.created_at, 'post_text':message.text}

                cmd = 'echo "' + message.text + '" | treetagger/cmd/tree-tagger-english > ./twitter_message_output.txt'
                os.system(cmd)

                pos_file = open('twitter_message_output.txt', 'r')
                tokens = []
                self.parse_string = ""
                for line in pos_file:
                     current_line = []
                     self.parse_string += line
                     for value in tokenize.whitespace(line):
                         current_line.append(value)
                     tokens.append(current_line)
                self.twitter_info = {'twitter_post_id':message.id,'twitter_author_id':message.user.id,'twitter_author_name':message.user.screen_name,'twitter_location':message.user.location}
                twitter_block = twitter_info_block % self.twitter_info
                self._AddFwiktrData(dict([('twitter_info_block',twitter_block)]))                                           
                self._AddFwiktrData(dict([('post_pos_output', cgi.escape("\n".join(["\t".join(i) for i in tokens])))]))                
                self._RetreiveFlickrURLs(tokens)
                self._PostDataToWeb()
                time.sleep(30)
            except UnicodeEncodeError:
                print "Twitter Message not ascii, skipping"        

    def _PostDataToWeb(self):
        xml_string = xml_block % (self.fwiktr_info)
        print xml_string
        self._curl.setopt(pycurl.URL, 'http://www.30helensagree.com/fwiktr/fwiktr_post.php')
        self._curl.setopt(pycurl.POST, 1)
        self._curl.setopt(pycurl.POSTFIELDS, urllib.urlencode([("fwiktr_post", xml_string)]))
#        self._curl.perform()

    def _IsTagNoun(self, tag_tuple):
        #Start by culling everything that's not a noun
        if tag_tuple[1] == "NP" or tag_tuple[1] == "NN" or tag_tuple[1] == "NNS":
            return True
        return False
            
    def _AddFwiktrData(self, new_dict):
        self.fwiktr_info = dict(self.fwiktr_info, **new_dict)

    def _RetreiveFlickrURLs(self, tagList):
        tag_string = ','.join([i[0] for i in filter(self._IsTagNoun, tagList)])

        rsp = self.fapi.photos_search(api_key=self._GetOption('flickr_api_key'),tags=tag_string)
        self.fapi.testFailure(rsp)
        if(rsp.photos[0]['total'] == 0): return 

        rand_index = random.randint(0, min(int(rsp.photos[0]['perpage']), int(rsp.photos[0]['total'])))
        self._AddFwiktrData(dict([('flickr_total', rsp.photos[0]['total']), ('post_tags', cgi.escape(tag_string))]))
        
	a = rsp.photos[0].photo[rand_index]
        self._AddFwiktrData(dict([('flickr_server', a['server']), ('flickr_farm', a['farm']), ('flickr_photoid', a['id']), ('flickr_secret', a['secret']), ('flickr_ownerid', a['owner']), ('flickr_title', cgi.escape(a['title']))]))

        
def main():
    f = Fwiktr()
    while 1:
        f.RunPOSTagger()
        time.sleep(60)

if __name__ == "__main__":
    main()
