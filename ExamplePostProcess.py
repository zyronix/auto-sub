#This Script is an example of what is possible with the
#PostProcess feature of Auto-Sub
import sys
import library.pythontwitter as twitter
import library.oauth2 as oauth
import socket
import email.utils
import smtplib

from library.growl import gntp
from email.mime.text import MIMEText

try:
    from urlparse import parse_qsl
except:
    from cgi import parse_qsl

# TODO: create notification library and integrate it

#OPTIONS EDIT HERE
#What options:
# twitter - send notifications to twitter
# growl - send notification to a growl server
# echo - echo's the arguments given to the script
# mail - send an email when a subtitle is downloaded

what = "echo"

#Growl Options:
growl_host = ""
growl_port = 23053
growl_pass = ""
#/Growl Options

#Twitter options:
token_key = ''
token_secret = ''
#/Twitter options

#Mail Options:
#WARNING! YOUR PASSWORD IS STORED IN PLAIN TEXT MAKE SURE THE FILE IS NOT
#READABLE BY EVERYONE.
#!USE AT OWN RISK!
srv = 'smtp.gmail.com:587'
fromaddr = 'example@gmail.com'
toaddrs = 'example@gmail.com'
username = 'example@gmail.com'
password = 'mysecretpassword'
subject = 'Subs info'
#/Mail Options


#/OPTIONS STOP EDITING BELOW THIS LINE
#MAIL APPLICATION SOURCE
def send_mail(message):
    """
    Construct and send the email.
    
    Keyword arguments:
    message -- Full name of the subtitle
    """
    msg = MIMEText('Hi,\n \n AutoSub downloaded the following subtitle:\n %s'\
                   % message)
    msg['To'] = email.utils.formataddr(('Recipient', toaddrs))
    msg['Subject'] = subject
    msg = msg.as_string()

    try:
        server = smtplib.SMTP(srv)
        server.starttls()
        server.login(username, password)
        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()
        print "Email notification send"
    except:
        print "ERROR: Unable to send an email notification. Check your email settings."


#GROWL APPLICATION SOURCE
def send_growl(host, port, message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(message)
        response = gntp.parse_gntp(s.recv(1024))
        s.close()
        print "Growl notification send"
    except socket.error:
        print "ERROR: Unable to send growl notification to growl server. Check your settings."


def create_growl(message):
    notice = gntp.GNTPNotice()
    notice.add_header('Application-Name', "AutoSub")
    notice.add_header('Notification-Name', "Subtitle Download")
    notice.add_header('Notification-Title', "AutoSub: Subtitle Download")
    notice.add_header('Notification-Text', message)
    if growl_pass != "":
        notice.set_password(growl_pass)
    send_growl(growl_host, growl_port, notice.encode())


def register_growl():
    register = gntp.GNTPRegister()
    register.add_header('Application-Name', "AutoSub")
    register.add_notification('Test', True)
    register.add_notification('Subtitle Download', True)
    if growl_pass != "":
        register.set_password(growl_pass)
    send_growl(growl_host, growl_port, register.encode())

    notice = gntp.GNTPNotice()
    notice.add_header('Application-Name', "AutoSub")
    notice.add_header('Notification-Name', "Test")
    notice.add_header('Notification-Title', "Testing notification")
    notice.add_header('Notification-Text', "This is a test notification send by AutoSub, check!")
    if growl_pass != "":
        notice.set_password(growl_pass)
    send_growl(growl_host, growl_port, notice.encode())

#TWITTER APPLICATION SOURCE
consumer_key = 'CRMvUogoJ5kMErtU9fiw'
consumer_secret = 'JqS5jJIWdokl5iijZmoBHNwRsknw7xmCxPggEsmo8'

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'


def authorize_application():
    consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
    oauth_client = oauth.Client(consumer)
    response, content = oauth_client.request(REQUEST_TOKEN_URL, 'GET')

    if response['status'] != '200':
        print "ERROR: Invalid response"
    else:
        request_token = dict(parse_qsl(content))
        print "Visit: " + AUTHORIZATION_URL + "?oauth_token=" + request_token['oauth_token']

    token_key = request_token['oauth_token']
    token_secret = request_token['oauth_token_secret']

    token = oauth.Token(token_key, token_secret)
    pin = raw_input('PIN: ').strip()
    token.set_verifier(pin)

    oauth_client2 = oauth.Client(consumer, token)
    response, content = oauth_client2.request(ACCESS_TOKEN_URL, method='POST', body='oauth_verifier=%s' % pin)
    access_token = dict(parse_qsl(content))

    if response['status'] != '200':
        print "ERROR: Invalid response"
    else:
        token_key = access_token['oauth_token']
        token_secret = access_token['oauth_token_secret']
        print "token_key='%s'" % token_key
        print "token_secret='%s'" % token_secret


def send_tweet(message):
    try:
        api = twitter.Api(consumer_key, consumer_secret, token_key, token_secret)
        api.PostUpdate(message)
        print "Tweet sended!"
    except:
        print "ERROR: Could not send tweet, make sure token_key & token_secret are correct."


#MAIN FUNCTION
if what == "echo":
    print
    try:
        print sys.argv[1]
        print sys.argv[2]
    except IndexError:
        print "ERROR: Trying to setup this script? Make sure you set the 'what' variable. "

if what == "twitter":
    if token_key == "":
        authorize_application()
    else:
        if (sys.argv[1] and sys.argv[2] and token_key != ""):
            var = sys.argv[1]

            var = var.split('/')
            tweet = "AutoSub Downloaded: " + var[-1]
            print "Sending the following tweet %s" % tweet[:140]
            send_tweet(tweet[:140])
        elif (sys.argv[1] and sys.argv[2]):
            print "ERROR: token_key not set yet, run script without any arguments"

if what == "growl":
    if len(sys.argv) == 1:
        register_growl()
    elif (sys.argv[1] and sys.argv[2] and growl_host != ""):
        var = sys.argv[1]
        var = var.split('/')
        create_growl(var[-1])

if what == "mail":
    if (sys.argv[1] and sys.argv[2] and srv != "" and fromaddr != "" and toaddrs != ""):
        var = sys.argv[1]
        var = var.split('/')
        send_mail(var[-1])
    elif (sys.argv[1] and sys.argv[2]):
        print "ERROR: Minimum mail settings aren't set."
    else:
        print "ERROR: Mail settings not set"
