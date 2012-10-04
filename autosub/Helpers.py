# Autosub Helpers.py - http://code.google.com/p/auto-sub/
#
# The Autosub helper functions
#

import logging
import re
import subprocess
from string import capwords
import time
import urllib2
import codecs
import os

from library import version
from autosub.version import autosubversion

import autosub

from autosub.Db import idCache
# Settings
log = logging.getLogger('thelogger')

REGEXES = [
        re.compile("^((?P<title>.+?)[. _-]+)?s(?P<season>\d+)[x. _-]*e(?P<episode>\d+)(([. _-]*e|-)(?P<extra_ep_num>(?!(1080|720)[pi])\d+))*[. _-]*((?P<quality>(1080|720|SD))*[pi]*[. _-]*(?P<source>(hdtv|dvdrip|bdrip|blu[e]*ray|web[. _-]*dl))*[. _]*(?P<extra_info>.+?)((?<![. _-])-(?P<releasegrp>[^-]+))?)?$", re.IGNORECASE),
        re.compile("^((?P<title>.+?)[\[. _-]+)?(?P<season>\d+)x(?P<episode>\d+)(([. _-]*x|-)(?P<extra_ep_num>(?!(1080|720)[pi])\d+))*[. _-]*((?P<quality>(1080|720|SD))*[pi]*[. _-]*(?P<source>(hdtv|dvdrip|bdrip|blu[e]*ray|web[. _-]*dl))*[. _]*(?P<extra_info>.+?)((?<![. _-])-(?P<releasegrp>[^-]+))?)?$", re.IGNORECASE),
        re.compile("^(?P<title>.+?)[. _-]+(?P<season>\d{1,2})(?P<episode>\d{2})([. _-]*(?P<quality>(1080|720|SD))*[pi]*[. _-]*(?P<source>(hdtv|dvdrip|bdrip|blu[e]*ray|web[. _-]*dl))*[. _]*(?P<extra_info>.+?)((?<![. _-])-(?P<releasegrp>[^-]+))?)?$", re.IGNORECASE)
        ]
SOURCE_PARSER = re.compile("(hdtv|tv|dvdrip|dvd|bdrip|blu[e]*ray|web[. _-]*dl)", re.IGNORECASE)
QUALITY_PARSER = re.compile("(1080|720|HD|SD)" , re.IGNORECASE)
LOG_PARSER = re.compile('^((?P<date>\d{4}\-\d{2}\-\d{2})\ (?P<time>\d{2}:\d{2}:\d{2},\d{3}) (?P<loglevel>\w+))', re.IGNORECASE)

def RunCmd(cmd):
    process = subprocess.Popen(cmd,
                            shell = True,
                            stdin = subprocess.PIPE,
                            stdout = subprocess.PIPE,
                            stderr = subprocess.PIPE)
    shell = process.stdout.read()
    shellerr = process.stderr.read()
    process.wait()
    return shell, shellerr

def CheckVersion():
    try:
        req = urllib2.Request(autosub.VERSIONURL)
        req.add_header("User-agent", autosub.USERAGENT) 
        resp = urllib2.urlopen(req,None,autosub.TIMEOUT)
        respone = resp.read()
        resp.close()
    except:
        log.error("checkVersion: The server returned an error for request %s" % autosub.VERSIONURL)
        return None
    try:
        match = re.search('(Alpha|Beta|Stable) (\d+)\.(\d+)\.(\d+)', respone)
        version_online = match.group(0)
    except:
        return None
    
    release = version_online.split(' ')[0]
    versionnumber = version.StrictVersion(version_online.split(' ')[1])
    
    running_release = autosubversion.split(' ')[0]
    running_versionnumber = version.StrictVersion(autosubversion.split(' ')[1])
    
    if release == running_release:
        if versionnumber > running_versionnumber:
            return True
        else:
            return False
    else:
        return None

def CleanSerieName(series_name):
    """Clean up series name by removing any . and _
    characters, along with any trailing hyphens.

    Is basically equivalent to replacing all _ and . with a
    space, but handles decimal numbers in string, for example:

    >>> cleanRegexedSeriesName("an.example.1.0.test")
    'an example 1.0 test'
    >>> cleanRegexedSeriesName("an_example_1.0_test")
    'an example 1.0 test'

    Stolen from dbr's tvnamer
    """
    try:
        series_name = re.sub("(\D)\.(?!\s)(\D)", "\\1 \\2", series_name)
        series_name = re.sub("(\d)\.(\d{4})", "\\1 \\2", series_name)  # if it ends in a year then don't keep the dot
        series_name = re.sub("(\D)\.(?!\s)", "\\1 ", series_name)
        series_name = re.sub("\.(?!\s)(\D)", " \\1", series_name)
        series_name = series_name.replace("_", " ")
        series_name = re.sub("-$", "", series_name)
        return capwords(series_name.strip())
    except TypeError:
        log.debug("CleanSerieName: There is no SerieName to clean")


def ReturnUpper(text):
    """
    Return the text converted to uppercase.
    When not possible return nothing.
    """
    try:
        text = text.upper()
        return text
    except:
        pass


def matchQuality(quality, item):
    if quality == u"SD":
        if re.search('720', item):
            log.debug("matchQuality: Quality SD did not match to %s" % item)
            return None
        elif re.search('1080', item):
            log.debug("matchQuality: Quality SD did not match to %s" % item)
            return None
        else:
            log.debug("matchQuality: Quality matched SD to %s" % item)
            return 1
    elif quality == u"1080p" and re.search('1080', item):
        log.debug("matchQuality: Quality is 1080 matched to %s" % item)
        return 1
    elif quality == u"720p" and re.search('720', item):
        log.debug("matchQuality: Quality is 720 matched to %s" % item)
        return 1


def scoreMatch(releasedict, release, quality, releasegrp, source, codec):
    """
    Return how high the match is. Currently 7 is the best match
    This function give the flexibility to change the most important attribute for matching or even give the user the possibility to set his own preference
    release is the filename as it is in the result from bierdopje
    If quality is matched, score increased with 2
    If releasegrp is matched, score is increased with 1
    If source is matched, score is increased with 4
    """
    score = 0
    log.debug("scoreMatch: Giving a matchscore for: %r. Try to match it with Q: %r GRP: %r S: %r" % (releasedict, quality, releasegrp, source))
    
    releasesource = None
    releasequality = None
    releasereleasegrp = None
    releasecodec = None
    
    if 'source' in releasedict.keys(): releasesource = releasedict['source']
    if 'quality' in releasedict.keys(): releasequality = releasedict['quality']
    if 'releasegrp' in releasedict.keys(): releasereleasegrp = releasedict['releasegrp']
    if 'codec' in releasedict.keys(): releasecodec = releasedict['codec']
    
    if releasegrp and releasereleasegrp:
        if releasereleasegrp == releasegrp:
            score += 1
    if source and releasesource:
        if releasesource == source:
            score += 8
    if quality and releasequality:
        if quality == releasequality:
            score += 4
    if codec and releasecodec:
        if codec == releasecodec:
            score += 2
    
    if not releasedict:
        log.warning("scoreMatch: Something went wrong, ProcessFileName could not process the file, %s, please report this!" %release)
        log.info("scoreMatch: Falling back to old matching system, to make sure you get your subtitle!")
        if releasegrp:
            if (re.search(re.escape(releasegrp), release, re.IGNORECASE)):
                score += 1
        if source:
            if (re.search(re.escape(source), release, re.IGNORECASE)):
                score += 8
        if quality:
            if (matchQuality(re.escape(quality), release)):
                score += 4
        if codec:
            if (re.search(re.escape(codec), release, re.IGNORECASE)):
                score += 2
         
    log.debug("scoreMatch: MatchScore is %s" % str(score))
    return score


def nameMapping(showName):
    if showName.upper() in autosub.USERNAMEMAPPINGUPPER.keys():
        log.debug("nameMapping: found match in user's namemapping for %s" % showName)
        return autosub.USERNAMEMAPPINGUPPER[showName.upper()]
    elif showName.upper() in autosub.NAMEMAPPINGUPPER.keys():
        log.debug("nameMapping: found match for %s" % showName)
        return autosub.NAMEMAPPINGUPPER[showName.upper()]


def SkipShow(showName, season, episode):
    if showName.upper() in autosub.SKIPSHOWUPPER.keys():
        log.debug("SkipShow: Found %s in skipshow dictonary" % showName)
        for seasontmp in autosub.SKIPSHOWUPPER[showName.upper()]:
            if seasontmp == '0':
                log.debug("SkipShow: variable of %s is set to 0, skipping the complete Serie" % showName)
                return True
            elif int(seasontmp) == int(season):
                log.debug("SkipShow: Season matches variable of %s, skipping season" % showName)
                return True


def getShowid(show_name):
    log.debug('getShowid: trying to get showid for %s' %show_name)
    show_id = nameMapping(show_name)
    if show_id:
        log.debug('getShowid: showid from namemapping %s' %show_id)
        return int(show_id)
    
    show_id = idCache().getId(show_name)
    if show_id:
        log.debug('getShowid: showid from cache %s' %show_id)
        if show_id == -1:
            log.error('getShowid: showid not found for %s' %show_name)
            return
        return int(show_id)
    
    #do we have enough api calls?
    if checkAPICalls(use=False):
        show_id = autosub.Bierdopje.getShowidApi(show_name)
    else:
        log.warning("getShowid: Out of API calls")
        return None
    
    if show_id:
        log.debug('getShowid: showid from api %s' %show_id)
        idCache().setId(show_id, show_name)
        log.info('getShowid: %r added to cache with %s' %(show_name, show_id))
        return int(show_id)
    
    log.error('getShowid: showid not found for %s' %show_name)
    idCache().setId(-1, show_name)


def checkAPICalls(use=False):
    """
    Checks if there are still API calls left
    Set true if a API call is being made.
    """
    currentime = time.time()
    lastrun  = autosub.APICALLSLASTRESET
    interval = autosub.APICALLSRESETINT
    
    if currentime - lastrun > interval:
        autosub.APICALLS = autosub.APICALLSMAX
        autosub.APICALLSLASTRESET = time.time()
    
    if autosub.APICALLS > 0:
        if use==True:
            autosub.APICALLS-=1
        return True
    else:
        return False

def DisplayLogFile(loglevel):
    maxLines = 500
    data = []
    if os.path.isfile(autosub.LOGFILE):
        f = codecs.open(autosub.LOGFILE, 'r', autosub.SYSENCODING)
        data = f.readlines()
        f.close()
    
    finalData = []
    
    numLines = 0
    
    for x in reversed(data):
        try:
            matches = LOG_PARSER.search(x)
            matchdic = matches.groupdict()
            if (matchdic['loglevel'] == loglevel.upper()) or (loglevel == ''):
                numLines += 1
                if numLines >= maxLines:
                    break
                finalData.append(x)
        except:
            continue
    result = "".join(finalData)
    return result

def ConvertTimestamp(datestring):
    date_object = time.strptime(datestring, "%Y-%m-%d %H:%M:%S")
    return "%02i:%02i:%02i %02i-%02i-%i" %(date_object[3], date_object[4], date_object[5], date_object[2], date_object[1], date_object[0])
    