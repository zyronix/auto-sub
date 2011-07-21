# AutoSub v6
#
# Created by wouterlucas.com
#
# What does it do?
# Scans a directory and checks if the TV Episode has a ".srt" file
# If not it will attempt to download the dutch version from bierdopje.com

import urllib
import urllib2
import os
import sys
import getopt
import time
import re
from xml.dom import minidom


# Settings ---------------------------------------------------------------------

# location of your TV Episodes
rootpath = "/mnt/nas1/content/TV"
# Set this to True if you also want the script to download the ENG version of the NLD is not available
# the english version will be named filename.eng.srt
fallbackToEng = True
# API key
apikey = "AFC34E2C2FE8B9F7"

#/Settings ---------------------------------------------------------------------

api = "http://api.bierdopje.com/%s/" %apikey
showid_cache = {}

def ProcessFile(file):
	print file, "start processing file name" 
	if re.search('[sS][0-9][0-9][eE][0-9][0-9]', file): 
		#s01e05
		result = re.search('[sS][0-9][0-9][eE][0-9][0-9]', file)
		episodeid = str(result.group(0))
		
		#episodeidstart = result.start(0) - 1
		episodeidstart = result.start(0)
		int(episodeidstart)
		
		season = episodeid[2]
		if episodeid[4] == "0":
			episode = episodeid[5]
		if not episodeid[4] == "0":
			episode = episodeid[4] + episodeid[5]
	
	if re.search('[0-9][0-9][0-9]', file):
		#105
		result = re.search('[0-9][0-9][0-9]', file)
		episodeid = str(result.group(0))
	
		#episodeidstart = result.start(0) - 1
		episodeidstart = result.start(0)
		int(episodeidstart)
		
		season = episodeid[0]
		if episodeid[1] == "0":
			episode = episodeid[2]
		if not episodeid[1] == "0":
			episode = episodeid[1] + episodeid[2]
			
	if re.search('[sS][0-9][0-9][xX][eE][0-9][0-9]', file):
		result = re.search('[sS][0-9][0-9][xX][eE][0-9][0-9]', file)

		#S00xE00
		episodeid = str(result.group(0))
		
		episodeidstart = result.start(0) - 1
		int(episodeidstart)
	
		season = episodeid[2]
		if episodeid[4] == "0":
			episode = episodeid[5]
		if not episodeid[4] == "0":
			episode = episodeid[4] + episodeid[5]
				
	if re.search('[0-9][xX][0-9][0-9]', file):
		#1x05
		result = re.search('[0-9][xX][0-9][0-9]', file)
		episodeid = str(result.group(0))
		
		episodeidstart = result.start(0) - 1
		int(episodeidstart)
	
		season = episodeid[0]
		if episodeid[2] == "0":
			episode = episodeid[3]
		if not episodeid[2] == "0":
			episode = episodeid[2] + episodeid[2]
	try:
		title = file[:episodeidstart]
		title = str.replace(title,"."," ")
		title = str.replace(title,"-"," ")
		title = str.replace(title," -","")
		title = str.replace(title,"- ","")
		title = title.rstrip()
		title = title.lstrip()
		title = str.title(title)
	
		return title, season, episode, episodeid
	except:
		print file, "error could not processfile name"
		exit()

	
def getShowid(showName):
	getShowIdUrl = "%sGetShowByName/%s" %(api, urllib.quote(showName))
	
	req = urllib2.urlopen(getShowIdUrl)
	dom = minidom.parse(req)
	req.close()
		
	if not dom or len(dom.getElementsByTagName('showid')) == 0 :
		return None
	
	showid = dom.getElementsByTagName('showid')[0].firstChild.data
	return showid

def getSubLink(showid, season, episode, lang, hdcontent):
	getSubLinkUrl = "%sGetAllSubsFor/%s/%s/%s/%s" %(api, showid, season, episode, lang)
	req = urllib2.urlopen(getSubLinkUrl)
	dom = minidom.parse(req)
	req.close()
	
	if not dom or len(dom.getElementsByTagName('result')) == 0 :
		return None
	
	for sub in dom.getElementsByTagName('result'):
		release = sub.getElementsByTagName('filename')[0].firstChild.data
		if release.endswith(".srt"):
			release = release[:-4]
			
		if hdcontent == True and re.search('720', release): 
			return sub.getElementsByTagName('downloadlink')[0].firstChild.data
		if hdcontent == True and re.search('1080', release): 
			return sub.getElementsByTagName('downloadlink')[0].firstChild.data
		if hdcontent == False: 
			if re.search('720', release): continue
			if re.search('1080', release): continue
			return sub.getElementsByTagName('downloadlink')[0].firstChild.data
		
while True:
	#print "Starting round of local disk checking"
	
	for dirname, dirnames, filenames in os.walk(os.path.join(rootpath)):
		for filename in filenames:			
			splitname = filename.split(".")
			ext = splitname[len(splitname)-1]
			
			if ext in ('avi','mkv','wmv','ts'):
				if re.search('sample', filename): continue
				
				srtfile = os.path.join(filename[:-4] + ".srt")
				engsrtfile = os.path.join(filename[:-4] + ".eng.srt") 
				
				if not os.path.exists(os.path.join(dirname,srtfile)):
					print filename, "Does not yet have a srt file."
					title, season, episode, episodeid = ProcessFile(filename)
					
					if title in showid_cache.keys():
						showid = showid_cache[title]
					
					if not title in showid_cache.keys():
						showid = getShowid(title)
						if not showid: 
							print filename, "Could not be found on bierdopje.com, skipping"
							continue
						
						#grab it from bierdopje.com
						showid_cache[title] = showid
					
					if ext in ('avi', 'ts', 'wmv'): hdcontent = False
					if ext in ('mkv'): hdcontent = True
					
					downloadLink = getSubLink(showid, season, episode, "nl", hdcontent)
					destsrt = os.path.join(dirname,srtfile)
					
					if not downloadLink:
						if fallbackToEng == False:
							#print filename, "No subtitles found on bierdopje.com, skipping"
							continue
						if os.path.exists(os.path.join(dirname,engsrtfile)) and fallbackToEng == True:
							#print filename, "The ENG subtitle is found, will try again later"
							continue
						if not os.path.exists(os.path.join(dirname,engsrtfile)) and fallbackToEng == True:
							#print filename, "Dutch subtitle could not be found on bierdopje.com, attempting to download the english version"
							downloadLink = getSubLink(showid, season, episode, "en", hdcontent)
							destsrt = os.path.join(dirname,engsrtfile)
							
							if not downloadLink:
								#print filename, "No subtitles found on bierdopje.com, skipping"
								continue
							
					if downloadLink:
						response = urllib2.urlopen(downloadLink)
						print "DOWNLOADING the following link:", downloadLink
						
						try:
							open(destsrt,'w').write(response.read())
						except:
							print filename, "Error while writing subtitle file. Aborting"
							exit()
						
						print "DOWNLOADED:", destsrt
	
	#print "Finished round of local disk checking"
	time.sleep(3600)
