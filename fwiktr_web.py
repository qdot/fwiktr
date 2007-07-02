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

fwiktr_block = '''<?xml version='1.0' standalone='yes'?>
<fwiktr>
    %(post_info_xml)s
    %(art_info_xml)s
    %(picture_info_xml)s
    %(post_source_info_xml)s
    %(picture_specific_info_xml)s
    <transforms>
      %(transform_info_xml)s
    </transforms>
</fwiktr>
'''

post_info_xml = '''
  <post>
    <post_source>%(post_source)s</post_source>
    <post_text>%(post_text)s</post_text>
    <post_date>%(post_date)s</post_date>
  </post>
'''

picture_info_xml = '''
  <picture>
	<picture_source>%(picture_source)s</picture_source>
  </picture>
'''

art_info_xml = '''
  <art>
    <art_tags>%(art_tags)s</art_tags>
  </art>
'''

transform_info_xml = '''
  <transform>
    <transform_step>%(transform_step)s</transform_step>
    <transform_index>%(transform_index)s</transform_index>
    <transform_before>%(transform_before)s</transform_before>
    <transform_after>%(transform_after)s</transform_after>
    <transform_output>%(transform_output)s</transform_output>
  </transform>
'''

twitter_info_xml = '''
  <post_info>
    <twitter_post_id>%(twitter_post_id)s</twitter_post_id>
    <twitter_author_id>%(twitter_author_id)s</twitter_author_id>
    <twitter_author_name>%(twitter_author_name)s</twitter_author_name>
    <twitter_location>%(twitter_location)s</twitter_location>
  </post_info>
'''

flickr_info_xml = '''
  <picture_info>
    <flickr_farm>%(flickr_farm)s</flickr_farm>
    <flickr_server>%(flickr_server)s</flickr_server>
    <flickr_photoid>%(flickr_photoid)s</flickr_photoid>
    <flickr_ownerid>%(flickr_ownerid)s</flickr_ownerid>
    <flickr_title>%(flickr_title)s</flickr_title>
    <flickr_secret>%(flickr_secret)s</flickr_secret>
  </picture_info>
'''

gCurl = pycurl.Curl()

class FwiktrServiceManager:
    def __init__(self):
        self._config = None
        self._SetupService()

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

#
# Post Services
#

class FwiktrPostRetriever(FwiktrServiceManager):
    def __init__(self):
        FwiktrServiceManager.__init__(self)
        self._msg_list = []
        self._current_msg = None

    def NextPost(self):
        #Iterate to the next post on the list. If we've exhausted the list, pull a new one        
        if len(self._msg_list) is 0:
            self._GetNewPosts()
        self._current_msg = self._msg_list.pop()

    def GetPostDate(self):
        raise Exception, "ONLY TO BE CALLED FROM CHILD CLASSES"

    def GetPostText(self):
        raise Exception, "ONLY TO BE CALLED FROM CHILD CLASSES"

    def GetPostXML(self):
        raise Exception, "ONLY TO BE CALLED FROM CHILD CLASSES"

    def _GetNewPosts(self):
        raise Exception, "ONLY TO BE CALLED FROM CHILD CLASSES"


class FwiktrTwitterRetriever(FwiktrPostRetriever):
    def __init__(self):
        FwiktrPostRetriever.__init__(self)

    def _SetupService(self):
        self._tapi = twitter.Api()

    def _GetNewPosts(self):
        self._msg_list = self._tapi.GetPublicTimeline()

    def GetPostDate(self):
        return self._current_msg.created_at

    def GetPostText(self):
        return self._current_msg.text

    def GetPostXML(self):
        message = self._current_msg
        self.twitter_info = {'twitter_post_id':message.id,'twitter_author_id':message.user.id,'twitter_author_name':message.user.screen_name,'twitter_location':message.user.location}
        return twitter_info_xml % self.twitter_info
        
#
# Picture Services
#

class FwiktrFlickrRetriever(FwiktrServiceManager):
    def __init__(self):
        self._pic_info = []
        FwiktrServiceManager.__init__(self)

    def _SetupService(self):
        self._fapi = FlickrAPI(self._GetOption('flickr_api_key'), self._GetOption('flickr_api_secret'))

    def GetPictureXML(self):
        flickr_info = dict([('flickr_server', self._pic_info['server']), ('flickr_farm', self._pic_info['farm']), ('flickr_photoid', self._pic_info['id']), ('flickr_secret', self._pic_info['secret']), ('flickr_ownerid', self._pic_info['owner']), ('flickr_title', cgi.escape(self._pic_info['title']))])
        return flickr_info_xml % flickr_info

    def GetNewPicture(self, tag_list):
        try:
            tag_string = ','.join(tag_list[0:19])
            if(tag_string == ""): return False
            rsp = self._fapi.photos_search(api_key=self._GetOption('flickr_api_key'),tags=tag_string)
            self._fapi.testFailure(rsp)        
            if(rsp.photos[0]['total'] == 0): return False
            rand_index = random.randint(0, min(int(rsp.photos[0]['perpage']), int(rsp.photos[0]['total'])))
            self._pic_info = rsp.photos[0].photo[rand_index]            
            return True 
        except:
            return False        

#
# Tag Services
#

class FwiktrTransformManager:
    def __init__(self):
        self._before = None
        self._after = None
        self._output = None
        self._step = None

    def SetStep(self, i):
        self._step = i

    def GetTransformXML(self):
        transform_info = {"transform_before":self._before, "transform_after":self._after, "transform_output":self._output, "transform_step":self._step, "transform_index":self._index}
        return transform_info_xml % transform_info

class FwiktrTokenize(FwiktrTransformManager):
    def __init__(self):
        self._index = 1

    def GetTagList(self, text):
        self._before = text
        tags = []
        [tags.append(i) for i in tokenize.whitespace(text)]
        self._output = ""
        self._after = tags
        return tags

class FwiktrTreeTagger(FwiktrTransformManager):
    def __init__(self):
        FwiktrTransformManager.__init__(self)

    def GetTagList(self, text):
        self._before = text
        self._output = ""
        cmd = "echo \"%s\" | treetagger/cmd/tree-tagger-english > ./twitter_message_output.txt" % text
        os.system(cmd)
        pos_file = open('twitter_message_output.txt', 'r')
        tokens = []
        self.parse_string = ""
        for line in pos_file:
            current_line = []
            self._output += line
            for value in tokenize.whitespace(line):
                current_line.append(value)
            tokens.append(current_line)
        
        self._output = self._output.replace("<unknown>", "[unknown]")
        filtered_tags = filter(self._ComparisonFunction, tokens)
        final_tags = []
        [final_tags.append(i[0]) for i in filtered_tags]
        self._after = final_tags
        return final_tags
   
    def _ComparisonFunction(self, list):
        raise Exception, "COMPARISON MUST BE DEFINED IN CHILD CLASS"

class FwiktrTreeTaggerNounsOnly(FwiktrTreeTagger):      
    def __init__(self):
        self._index = 2
        FwiktrTreeTagger.__init__(self)

    def _ComparisonFunction(self, list):
        return self._IsTagNoun(list)

    def _IsTagNoun(self, tag_tuple):
        #Start by culling everything that's not a noun
        if tag_tuple[1] in ["NP", "NN", "NNS", "NPS"]:
            return True
        return False

#
# Seasoning Services
#

#
# Weather Seasoner
#

#
# Google Recommendation Seasoner
#

#
# Main Functionality
#

class Fwiktr:
    def __init__(self):
        self._post_rets = [FwiktrTwitterRetriever()]
        self._pic_rets = [FwiktrFlickrRetriever()]
        self._tag_rets = [FwiktrTokenize(), FwiktrTreeTaggerNounsOnly()]
    def CreateArt(self):
        xml_info = dict()

        #Pull post from source
        post_ret = self._post_rets[0]
        post_ret.NextPost()
        try:
            post_text = str(post_ret.GetPostText())        
        except:
            print "Non-ASCII Message, skipping"
            return

        #Identify source's language

        #Pull tags from source

        tag_ret = self._tag_rets[1]
        tag_ret.SetStep(1)
        tag_list = tag_ret.GetTagList(post_text)

        xml_info["transform_info_xml"] = tag_ret.GetTransformXML()

        #Season tag list

        #Retrieve picture using tags
        
        pic_ret = self._pic_rets[0]
        if pic_ret.GetNewPicture(tag_list) is False: return

        #Post data to web

        picture_info_dict = {'picture_source':1}
        xml_info["picture_info_xml"] = picture_info_xml % picture_info_dict
        art_info_dict = {'art_tags':",".join(tag_list)}
        xml_info["art_info_xml"] = art_info_xml % (art_info_dict)
        post_info_dict = {'post_source':1, 'post_date':post_ret.GetPostDate(), 'post_text':cgi.escape(post_text)}
        xml_info["post_info_xml"] = post_info_xml % (post_info_dict)

        xml_info["post_source_info_xml"] = post_ret.GetPostXML()
        xml_info["picture_specific_info_xml"] = pic_ret.GetPictureXML()

        fwiktr_info = fwiktr_block % xml_info

        self._PostDataToWeb(fwiktr_info)
                
    def _PostDataToWeb(self, info):
        try:
            print info
            gCurl.setopt(pycurl.URL, 'http://www.30helensagree.com/fwiktr/fwiktr_post.php')
            gCurl.setopt(pycurl.POST, 1)
            gCurl.setopt(pycurl.POSTFIELDS, urllib.urlencode([("fwiktr_post", info)]))
            gCurl.perform()
        except:
            return

def main():
    f = Fwiktr()
    i = 0
    while i < 5:
        try:
            f.CreateArt()
            i = i + 1
        except KeyboardInterrupt:
            return
#    time.sleep(60)

if __name__ == "__main__":
    main()
