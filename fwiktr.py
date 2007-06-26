import time
import os
import sys
import twitter
import urllib
import math
import Image
import random
import ftplib
import uuid
import pycurl
from flickrapi import FlickrAPI
from nltk import tag, corpora, tokenize

flickrAPIKey = "2ccf0e610c963a8ac0b09ed3d6e07285"
flickrAPISecret = "246aca42330885ce"

file_header = '''
<HTML>
<HEAD>
<TITLE>fwiktr output for %s</TITLE>
</HEAD>
<BODY>
'''

file_footer = '''
</BODY>
</HTML>
'''

class Fwiktr:
    def __init__(self):
        self.ftp_socket = ftplib.FTP('30helensagree.com')
        self.ftp_socket.login('thirtyhelens', 'ZHXK7tzL')
        self.ftp_socket.cwd('30helensagree.com')
        self.SetupFlickr()
        self.SetupTwitter()

    def SetupFlickr(self):
        # make a new FlickrAPI instance
        self.fapi = FlickrAPI(flickrAPIKey, flickrAPISecret)

    def SetupTwitter(self):
        self.tapi = twitter.Api()        

    def RunPOSTagger(self):
        twitter_messages = self.tapi.GetPublicTimeline()
        for message in twitter_messages:
            try:

                cmd = 'echo "' + message.text + '" | treetagger/cmd/tree-tagger-english > ./twitter_message_output.txt'
                os.system(cmd)
                self.pos_file = open('twitter_message_output.txt', 'r')
                tokens = []
                self.parse_string = ""
                for line in self.pos_file:
                    current_line = []
                    self.parse_string += line + "<BR>"
                    for value in tokenize.whitespace(line):
                        current_line.append(value)
                    tokens.append(current_line)

                filename = uuid.uuid4()                
                self.output_file = open(str(filename)+".html", 'w')
                self.output_file.write(file_header % (message.text))
                self.output_file.write(message.text + "<BR>")
                
                self.RetreiveFlickrURLs(tokens)

                self.output_file.write(file_footer)
                self.output_file.close()
                self.output_file = open(str(filename)+".html", 'r')
                self.ftp_socket.storlines("STOR "+str(filename)+".html", self.output_file)
                self.output_file.close()
                self.pos_file.close()
                time.sleep(30)
            except UnicodeEncodeError:
                print "Twitter Message not ascii, skipping"        
            except AttributeError:
                print "Weird XML error. I wish it'd stop doing that"

    def CullAndFormatTagList(self, tagList):
        #Start by culling everything that's not a noun
        tags_culled = "";
        for tag_tuple in tagList:
            if tag_tuple[1] == "NP" or tag_tuple[1] == "NN" or tag_tuple[1] == "NNS":
                tags_culled += tag_tuple[0] + ","
        return tags_culled

    def RetreiveFlickrURLs(self, tagList):
        tag_string = self.CullAndFormatTagList(tagList)

        rsp = self.fapi.photos_search(api_key=flickrAPIKey,tags=tag_string)

        if(rsp.photos[0]['total'] == 0): return 
        rand_index = random.randint(0, min(int(rsp.photos[0]['perpage']), int(rsp.photos[0]['total'])))
        i = 0        

        urls = "<UL>"
	for a in rsp.photos[0].photo:            
            photo_url = "http://farm%s.static.flickr.com/%s/%s_%s.jpg" % (a['farm'], a['server'], a['id'], a['secret'])
            flickr_url = "http://www.flickr.com/photos/%s/%s" % (a['owner'], a['id'])
            urls += "<LI><A HREF='"+photo_url+"'>"+photo_url+"</A> - <A HREF='"+ flickr_url+"'>"+flickr_url+"</A></LI>"
            if i == rand_index:
                self.output_file.write("<A HREF='"+flickr_url+"'><IMG SRC='"+photo_url+"' border=0></A>")
            i = i + 1
        urls += "</UL>"
        self.output_file.write("<HR>")
        self.output_file.write(self.parse_string)
        self.output_file.write("<HR>")
        self.output_file.write("Tag String for Flickr Search: " + tag_string)
        self.output_file.write("<HR>")
        self.output_file.write("Using photo " + str(rand_index) + " of " + rsp.photos[0]['total']  + "<BR>")
        self.output_file.write("Selection method: RANDOM CHOICE<BR>")
        self.output_file.write(urls)
def main():
    f = Fwiktr()
    while 1:
        f.RunPOSTagger()
        print "Resting..."
        time.sleep(60)

if __name__ == "__main__":
    main()
