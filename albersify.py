#!/usr/bin/python
import boto
import pycurl
import urllib
import simplejson as json
import cStringIO
import Image, ImageDraw
import sys
import logging, os
from random import randint
import urlparse
import oauth2 as oauth
from apscheduler.scheduler import Scheduler

s3_key = os.environ['S3_KEY']
s3_secret = os.environ['S3_SECRET']
s3_bucket = os.environ['S3_BUCKET']
tumblr_blog = os.environ['TUMBLR_BLOG']
api_token = os.environ['CH_API_KEY']

consumer_key = os.environ['TUMBLR_CONSUMER_KEY']
consumer_secret = os.environ['TUMBLR_CONSUMER_SECRET']
oauth_key = os.environ['TUMBLR_OAUTH_KEY']
oauth_secret = os.environ['TUMBLR_OAUTH_SECRET']

request_token_url = 'http://www.tumblr.com/oauth/request_token'
access_token_url = 'http://www.tumblr.com/oauth/access_token'
authorize_url = 'http://www.tumblr.com/oauth/authorize'

logging.basicConfig()
sched = Scheduler()
 
def create_post():
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

	# build the image / write it to S3

	conn = boto.connect_s3(s3_key, s3_secret)
	bucket = conn.create_bucket(s3_bucket)
	from boto.s3.key import Key
	k = Key(bucket)
	k.key = 'albers.png'

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

	out_im = cStringIO.StringIO()
	im.save(out_im, 'PNG')

	k.set_contents_from_string(out_im.getvalue())
	k.set_acl('public-read')

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
        'source' : 'https://s3.amazonaws.com/encodedcatalog/albers.png',
        'link' : object_link,
        'tags' : tags,
        'slug' : object_id,
		}

	blog = 'http://api.tumblr.com/v2/blog/' + tumblr_blog + '/post'

	print client.request(blog, method="POST", body=urllib.urlencode(params))

    
@sched.cron_schedule(hour='*')
def scheduled_job():
	create_post()

def run_clock():
	sched.start()

	while True:
		pass

if __name__ == "__main__":
	
	import sys
		
	if len(sys.argv) > 1:
		if (sys.argv[1] == "timed"):
			run_clock()
	
	create_post()

