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
from xml.parsers.xmlproc import xmlval
from flickrapi import FlickrAPI
from nltk import tag, corpora, tokenize


fwiktr_xml = '''<?xml version="1.0"?>
<!DOCTYPE fwiktr SYSTEM "fwiktr.dtd">
<fwiktr>
  <language>
    <language_method>%(language_method)s</language_method>
    <language_description>%(language_description)s</language_description>
    <language_output>%(language_output)s</language_output>
    <language_result>%(language_result)s</language_result>
  </language>
  <art>
    %(art_tags)s
  </art>
  <post>
    <post_author_name>%(post_author_name)s</post_author_name>
    <post_location>%(post_location)s</post_location>
    <post_text>%(post_text)s</post_text>
    <post_date>%(post_date)s</post_date>
    %(post_info)s
  </post>
  <picture>
    <picture_title>%(picture_title)s</picture_title>
    %(picture_info)s
  </picture>
  <transforms>
    %(transforms)s
  </transforms>
</fwiktr>
'''

transform_info_xml = '''
  <transform>
    <transform_name>%(transform_name)s</transform_name>
    <transform_description>%(transform_description)s</transform_description>
    <transform_step>%(transform_step)s</transform_step>
    <transform_before>%(transform_before)s</transform_before>
    <transform_after>%(transform_after)s</transform_after>
    <transform_output>%(transform_output)s</transform_output>
  </transform>
'''

twitter_info_xml = '''
  <twitter>
    <twitter_post_id>%(twitter_post_id)s</twitter_post_id>
    <twitter_author_id>%(twitter_author_id)s</twitter_author_id>
  </twitter>
'''

flickr_info_xml = '''
  <flickr>
    <flickr_farm>%(flickr_farm)s</flickr_farm>
    <flickr_server>%(flickr_server)s</flickr_server>
    <flickr_photo_id>%(flickr_photo_id)s</flickr_photo_id>
    <flickr_owner_id>%(flickr_owner_id)s</flickr_owner_id>
    <flickr_secret>%(flickr_secret)s</flickr_secret>
  </flickr>
'''

gCurl = pycurl.Curl()

def OutputTagList(tag_list):
    return "<tags>" + ''.join( [("<tag>%s</tag>"%i) for i in tag_list] ) + "</tags>"

class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable

#
# Base Classes
#

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

class FwiktrTransformManager:
    step = 0
    transform_xml = ""

    def __init__(self):
        self._before = None
        self._after = None
        self._output = None
        self._description = "Generic Transform Description. PLEASE CHANGE."
        self._name = "Generic Transform Name. PLEASE CHANGE."

    def ClearTransformInfo():
        FwiktrTransformManager.step = 0
        FwiktrTransformManager.transform_xml = ""
    ClearTransformInfo = Callable(ClearTransformInfo)

    def AddTransformInfo(self):
        FwiktrTransformManager.transform_xml += self._BuildTransformXML()
        FwiktrTransformManager.step = FwiktrTransformManager.step + 1

    def RunTransform(self, transform_data):
        if isinstance(transform_data, list):
            self._before = transform_data
        else:
            self._before = []
        self._after = self._Run(transform_data)
        self.AddTransformInfo()
        return self._after

    def _Run(self, transform_data):
        raise Exception, "ONLY TO BE CALLED FROM CHILD CLASSES"

    def GetTransformXML(self):
        return FwiktrTransformManager.transform_xml

    def _BuildTransformXML(self):
        transform_info = {"transform_before":OutputTagList(self._before), "transform_after":OutputTagList(self._after), "transform_output":self._output, "transform_step":FwiktrTransformManager.step, "transform_name":self._name, "transform_description":self._description}
        return transform_info_xml % transform_info

#
# Post Services
#

class FwiktrPostRetriever(FwiktrServiceManager):
    def __init__(self):
        FwiktrServiceManager.__init__(self)
        self._msg_list = []
        self._current_msg = None
        self.name = ""

    def NextPost(self):
        #Iterate to the next post on the list. If we've exhausted the list, pull a new one        
        if len(self._msg_list) is 0:
            self._GetNewPosts()
        self._current_msg = self._msg_list.pop()

    def GetPostDate(self):
        raise Exception, "ONLY TO BE CALLED FROM CHILD CLASSES"

    def GetPostText(self):
        raise Exception, "ONLY TO BE CALLED FROM CHILD CLASSES"

    def GetPostData(self):
        return {'post_author_name':self._current_msg.user.screen_name,'post_location':self._current_msg.user.location,'post_info':self._GetPostSpecificXML()}

    def _GetPostSpecificXML(self):
        raise Exception, "ONLY TO BE CALLED FROM CHILD CLASSES"

    def _GetNewPosts(self):
        raise Exception, "ONLY TO BE CALLED FROM CHILD CLASSES"

class FwiktrTwitterRetriever(FwiktrPostRetriever):
    def __init__(self):
        FwiktrPostRetriever.__init__(self)
        self.name = "Twitter"

    def _SetupService(self):
        self._tapi = twitter.Api()

    def _GetNewPosts(self):
        self._msg_list = self._tapi.GetPublicTimeline()

    def GetPostDate(self):
        return self._current_msg.created_at

    def GetPostText(self):
        return self._current_msg.text

    def _GetPostSpecificXML(self):
        return twitter_info_xml % {'twitter_post_id':self._current_msg.id,'twitter_author_id':self._current_msg.user.id}

#
# Picture Services
#

class FwiktrFlickrFuckItSelectionTransform(FwiktrTransformManager):
    def __init__(self):
        self._description = "Uses the 'ANY' (Universal OR) search to seed the picture search, then selects a random picture."
        self._name = "Flickr 'Fuck It' Selector"
    def _RunTransform(self, transform_data):
        return

class FwiktrFlickrFullANDSelectionTransform(FwiktrTransformManager):
    def __init__(self):
        self._description = "Uses the 'ALL' (Universal AND) search to seed the picture search, then selects a random picture if there are results. If not, falls back to 'Fuck It' search."
        self._name = "Flickr 'Full AND' Selector"
    def _RunTransform(self, transform_data):
        return
        
class FwiktrFlickrTagCullTransform(FwiktrTransformManager):
    def __init__(self):
        self._description = "Culls tag list down to 20 tags (maximum allowed by flickr API)"
        self._name = "Flickr Tag Cull Transformer"
    def _RunTransform(self, transform_data):
        return tag_list[0:19]
        
class FwiktrFlickrRetriever(FwiktrServiceManager):
    transformList = [FwiktrFlickrFuckItSelectionTransform(), FwiktrFlickrFullANDSelectionTransform()]
    def __init__(self):
        self._pic_info = []
        FwiktrServiceManager.__init__(self)
        self.name = "Flickr"

    def _SetupService(self):
        self._fapi = FlickrAPI(self._GetOption('flickr_api_key'), self._GetOption('flickr_api_secret'))

    def GetPictureXML(self):
        return flickr_info_xml

    def GetPictureData(self):
        return {'picture_title':cgi.escape(self._pic_info['title']), 'picture_info':self._GetPictureSpecificData()}
        
    def _GetPictureSpecificData(self):
        return flickr_info_xml % {'flickr_server':self._pic_info['server'], 'flickr_farm':self._pic_info['farm'], 'flickr_photo_id':self._pic_info['id'], 'flickr_secret':self._pic_info['secret'], 'flickr_owner_id':self._pic_info['owner']}

    def GetNewPicture(self, tag_list):
        try:
            if len(tag_list) > 20:
                culler = FwiktrFlickrTagCullTransform()
                tag_list = culler.RunTransform(tag_list)
            tag_string = ','.join(tag_list)
            if(tag_string == ""): return False
            rsp = self._fapi.photos_search(api_key=self._GetOption('flickr_api_key'),tags=tag_string)
            self._fapi.testFailure(rsp)
            if(rsp.photos[0]['total'] == 0): return False
            rand_index = random.randint(0, min(int(rsp.photos[0]['perpage']), int(rsp.photos[0]['total'])))
            self._pic_info = rsp.photos[0].photo[rand_index]            
            return True 
        except:
            return False        
#            raise
#
# Tag Services
#

class FwiktrTokenize(FwiktrTransformManager):
    def __init__(self):
        self._description = "Tokenizer from Python NLP Toolkit. Removes all punctuation and whitespace, gives back tokenized word list with no filtering."
        self._name = "NLPK Tokenizer"

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

    def _Run(self, text):
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
        return final_tags
   
    def _ComparisonFunction(self, list):
        raise Exception, "COMPARISON MUST BE DEFINED IN CHILD CLASS"

class FwiktrTreeTaggerPOSPicker(FwiktrTreeTagger):
    def __init__(self):
        FwiktrTreeTagger.__init__(self)
        self._poslist = []
    
    def _ComparisonFunction(self, list):
        #Start by culling everything that's not a noun
        if list[1] in self._poslist:
            return True
        return False      

class FwiktrTreeTaggerNounsOnly(FwiktrTreeTaggerPOSPicker):      
    def __init__(self):
        FwiktrTreeTaggerPOSPicker.__init__(self)
        self._poslist = ["NP", "NN", "NNS", "NPS"]
        self._name = "TreeTagger - Nouns Only"
        self._description = "Return only words having Parts of Speech type NN, NP, NNS, or NPS, as identified by TreeTagger (http://www.ims.uni-stuttgart.de/projekte/corplex/TreeTagger/)"

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


def CombineDictionaries(dict1, dict2):
    return dict(dict1, **dict2)

class Fwiktr:
    def __init__(self):
        self._post_rets = [FwiktrTwitterRetriever()]
        self._pic_rets = [FwiktrFlickrRetriever()]
        self._tag_rets = [FwiktrTokenize(), FwiktrTreeTaggerNounsOnly()]
    def CreateArt(self):
        FwiktrTransformManager.ClearTransformInfo()
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
        tag_list = tag_ret.RunTransform(post_text)

        print tag_list

        #Season tag list

        #Retrieve picture using tags
        
        pic_ret = self._pic_rets[0]
        if pic_ret.GetNewPicture(tag_list) is False: return

        #Build XML blob

        xml_dict = {'language_method':"No Detection - English", 'language_result':"English", 'language_output':"", 'language_description':"No processing done, assumes english", 'art_tags':OutputTagList(tag_list), 'post_date':post_ret.GetPostDate(), 'post_text':cgi.escape(post_text), 'transforms':tag_ret.GetTransformXML()}
        xml_dict = CombineDictionaries(xml_dict, post_ret.GetPostData())
        xml_dict = CombineDictionaries(xml_dict, pic_ret.GetPictureData())

        xml_info["transform_info_xml"] = tag_ret.GetTransformXML()

        fwiktr_info = fwiktr_xml % xml_dict
        print fwiktr_info

        #check the validity of our XML before we ship it off
        try:
            parser=xmlval.XMLValidator()
            parser.feed(fwiktr_info)
        except:
#            raise
            return
        
        #Post data to web

        self._PostDataToWeb(fwiktr_info)
                
    def _PostDataToWeb(self, info):
        try:
            gCurl.setopt(pycurl.URL, 'http://www.30helensagree.com/fwiktr/fwiktr_post.php')
            gCurl.setopt(pycurl.POST, 1)
            gCurl.setopt(pycurl.POSTFIELDS, urllib.urlencode([("fwiktr_post", info)]))
            gCurl.perform()
        except:
            return

def main():
    f = Fwiktr()
    i = 0
    while  i < 10:
        try:
            f.CreateArt()
            i = i + 1
        except KeyboardInterrupt:
            return
    time.sleep(60)

if __name__ == "__main__":
    main()
