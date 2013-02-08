#!/usr/bin/env python

import glob
import pycurl
import urllib
import simplejson as json
import cStringIO
import Image, ImageDraw
import sys
import os
from random import randint
import urlparse
import oauth2 as oauth

api_token = 'YOUR-COOPER-HEWITT-API-KEY'

consumer_key = 'YOUR-TUMBLR-CONSUMER-KEY'
consumer_secret = 'YOUR-TUMBLR-CONSUMER-SECRET'
oauth_key = 'YOUR-TUMBLR-OAUTH-KEY'
oauth_secret = 'YOUR-TUMBLR-OAUTH-SECRET'

request_token_url = 'http://www.tumblr.com/oauth/request_token'
access_token_url = 'http://www.tumblr.com/oauth/access_token'
authorize_url = 'http://www.tumblr.com/oauth/authorize'
 
buf = cStringIO.StringIO()
 
c = pycurl.Curl()
c.setopt(c.URL, 'https://api.collection.cooperhewitt.org/rest')
d = {'method':'cooperhewitt.objects.getRandom','access_token':api_token}

c.setopt(c.WRITEFUNCTION, buf.write)

c.setopt(c.POSTFIELDS, urllib.urlencode(d) )
c.perform()

random = json.loads(buf.getvalue())

buf.reset()
buf.truncate()

object_id = random.get('object', [])
object_id = object_id.get('id', [])

print object_id

d = {'method':'cooperhewitt.objects.getAlbers','id':object_id ,'access_token':api_token}

c.setopt(c.POSTFIELDS, urllib.urlencode(d) )
c.perform()

albers = json.loads(buf.getvalue())

rings = albers.get('rings',[])
ring1color = rings[0]['hex_color']
ring2color = rings[1]['hex_color']
ring3color = rings[2]['hex_color']

ring1id = rings[0]['value']
ring2id = rings[1]['value']
ring3id = rings[2]['value']

print ring1color, ring2color, ring3color

buf.close()

# build the image / write it to disk

size = (1000,1000)             
im = Image.new('RGB', size, ring1color) 
draw = ImageDraw.Draw(im)

ring2coordinates = ( randint(50,100), randint(50,100) , randint(900, 950), randint(900,950))

print ring2coordinates

ring3coordinates = ( randint(ring2coordinates[0]+50, ring2coordinates[0]+100) , randint(ring2coordinates[1]+50, ring2coordinates[1]+100) ,  randint(ring2coordinates[2]-200, ring2coordinates[2]-50) , randint(ring2coordinates[3]-200, ring2coordinates[3]-50) )

print ring3coordinates

draw.rectangle(ring2coordinates, fill=ring2color)
draw.rectangle(ring3coordinates, fill=ring3color)  
                      
del draw 

im.save('../www/albers.png', 'PNG')

consumer = oauth.Consumer(consumer_key, consumer_secret)
client = oauth.Client(consumer)

resp, content = client.request(request_token_url, "GET")
if resp['status'] != '200':
        raise Exception("Invalid response %s." % resp['status'])

request_token = dict(urlparse.parse_qsl(content))

token = oauth.Token(oauth_key, oauth_secret)
client = oauth.Client(consumer, token)

whoami = os.path.abspath(sys.argv[0])
bindir = os.path.dirname(whoami)

object_link = 'http://collection.cooperhewitt.org/objects/'+object_id
tags = 'ch:object=' + object_id + ', ' + ring1id + ', ' + ring2id + ', ' + ring3id

params = {
        'type' : 'photo',
        'source' : 'http://YOUR-WEBSITE.com/albers.png',
        'link' : object_link,
        'tags' : tags,
        'slug' : object_id,
}

print client.request("http://api.tumblr.com/v2/blog/YOUR-TUMBLR-URL.tumblr.com/post", method="POST", body=urllib.urlencode(params))

    

