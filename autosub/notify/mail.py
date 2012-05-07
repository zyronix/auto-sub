import logging

import email.utils
import smtplib
from email.mime.text import MIMEText

import autosub

log = logging.getLogger('thelogger')

def send_notify(lang, subtitlefile, videofile):
    log.debug("Mail: Trying to send a mail")
    message = MIMEText("""Hi,\n 
\n 
AutoSub downloaded the following subtitle (language: %s):\n 
%s\n
For the videofile:\n
%s\n
    """ %(lang, subtitlefile, videofile))
    message['To'] = email.utils.formataddr(('Recipient', autosub.MAILTOADDR))
    message['Subject'] = autosub.MAILSUBJECT
    message = message.as_string()
    try:
        server = smtplib.SMTP(autosub.MAILSRV)
        if autosub.MAILENCRYPTION == u'TLS':
            server.starttls()
        if autosub.MAILUSERNAME != '' and autosub.MAILPASSWORD != '':
            server.login(autosub.MAILUSERNAME, autosub.MAILPASSWORD)
        server.sendmail(autosub.MAILFROMADDR, autosub.MAILTOADDR, message)
        server.quit()
        log.info("Mail: Mail sended")
        return True
    except:
        log.error("Mail: Failed to send a mail")
        return False
        
def test_notify():
    log.debug("Mail: Trying to send a mail")
    message = MIMEText('Testing AutoSub and mail notify \n Everything seems to be ok!')
    message['To'] = email.utils.formataddr(('Recipient', autosub.MAILTOADDR))
    message['Subject'] = 'AutoSub: Testing 1-2-3'
    message = message.as_string()
    try:
        server = smtplib.SMTP(autosub.MAILSRV)
        if autosub.MAILENCRYPTION == u'TLS':
            server.starttls()
        if autosub.MAILUSERNAME != '' and autosub.MAILPASSWORD != '':
            server.login(autosub.MAILUSERNAME, autosub.MAILPASSWORD)
        server.sendmail(autosub.MAILFROMADDR, autosub.MAILTOADDR, message)
        server.quit()
        log.info("Mail: Mail sended")
        return True
    except:
        log.error("Mail: Failed to send a mail")
        return False