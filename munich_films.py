#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Code for web-scraping the Munich film listings from www.artechock.de
#
# Requirements:
#    Python 3.x
#    requests 2.x ("pip install requests")
#    BeautifulSoup 4.x ("pip install beautifulsoup4")

# TODO
#
# [ ] Create simpler film-time listings
#
# [ ] Merge 3D and non-3D versions of same film?
#
# [ ] Add current date (default) output filename from artechock.de site?
#
#
# Really speculative
# [X] Option to include German-language films
#
# [ ] Create HTML version with links to IMDB pages on films
#

from __future__ import print_function

import sys, optparse, copy, time
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup

# possibly we can use lxml in the future, but BeautifulSoup can't seem to find it...
parserName = "html.parser"
# try:
# 	import lxml
# 	parserName = "lxml"
# except ImportError:
# 	parserName = "html.parser"


artechockURL = "http://www.artechock.de/film/muenchen/oton.htm"

testTextVersion = "/Users/erwin/Desktop/artechock_originalton.html"

GERMAN_DAILY = "tgl."
GERMAN_EXCEPT = u'außer'
DAYS_TO_ENGLISH = {"So.": "Sun", "Mo.": "M", "Di.": "Tu", "Mi.": "W", "Do.": "Th",
					"Fr.": "F", "Sa.": "Sat"}

TAGEN = ["So.", "Mo.", "Di.", "Mi.", "Do.", "Sa."]


# EXAMPLES OF THEATER TIME LISTINGS:
# 'tgl. 17:15'
# 'tgl. 20:50 (Mi. 21:15)', ' Di. auch 12:30'
# 'tgl. 15:00, 17:45, 20:30 (außer Mo.)'
# 'tgl. außer Di. 22:55\n    \n     (\n     \n      artechock-Kritik\n     \n     )'
# 'tgl. außer Mi. 17:20; So. auch 12:10; Mi. 17:00'
# 'tgl. 16:20, 20:50 (außer Mo./Mi.); Fr./Sa. auch 23:00\n  ...'
# 'tgl. 19:00 (So. 19:30)'
# 'Mo. 20:00'
# 'Sa./So. 20:00'
# 'Fr.-So. 14:30'
# 'Fr./Mo./Mi. 21:00\n  ...'
# 'So. 11:00'
# 'So. 11:00 (mit Pause)'
# 'Do. 19:30; So. 16:00'
# 'So. 21:00; Mi. 18:30 (+Vorfilm »Drei Minuten in einem Film von Ozu«)'
# 
# day specifications: single | single/single | single/single/single | single-single


def TranslateDays( string ):
	for Tag in TAGEN:
		string = string.replace(Tag, DAYS_TO_ENGLISH[Tag])
	return string

def TranslateTimesSimple( theaterTime ):
	"""Given a tuple of(theaterName, movie showtimes) in German, returns movie showtimes
	in English.
	"""
	showtimes = theaterTime[1]
	# strip off extra stuff (some lines have extra spaces and \n)
	showtimesClean = showtimes.splitlines()[0].rstrip()
	showtimesClean.lstrip()
	# translate to English
	showtimesClean = showtimesClean.replace("tgl.", "daily")
	showtimesClean = showtimesClean.replace(u"außer", "except")
	showtimesClean = showtimesClean.replace("auch", "also")
	showtimesClean = TranslateDays(showtimesClean)
	return showtimesClean
	
	
def GetTitle( text ):
	"""Given a bit of text which has a form like this:
		'\n\n      Film Title\n     \n     (OmU)\n    '
	return just the film title.
	"""
	pp = text.splitlines()
	pp2 = [p.strip() for p in pp if len(p.strip()) > 1]
	return pp2[0]

def GetTheater( soup ):
	"""Given a BeautifulSoup object corresponding to a table row containing
	theater name and showtimes, extract the theater name.
	"""
	# safest thing is to look for "link" class within "mid b" column
	midCol = soup.find("td", {"class": "mid b"})
	link = midCol.find("span", {"class": "link"})
	return link.getText()
	
def GetShowTimes( soup ):
	"""Given a BeautifulSoup object corresponding to a table row containing
	theater name and showtimes, extract the showtimes.
	"""
	timesBlob = soup.find_all("td", {"class": "right"})[0]
	# get rid of Unicode non-breaking spaces
	showTimes = timesBlob.getText()
	showTimes = showTimes.replace(u'\xa0', u' ')
	return showTimes
	
def GetTheatersAndTimes( filmSoup ):
	"""Given a BeautifulSoup object corresponding to the set of table rows
	for a given film, extract the theater names and corresponding showtimes.
	
	Returns a list of tuples:
		[(theater1, showtimes1), (theater2, showtimes2), ...]
	"""
	# all films have at least a "start" table row ('class="start"')
	startStuff = filmSoup.find_all("tr", {"class": "start"})[0]
	theaterName = GetTheater(startStuff)
	showTimes = GetShowTimes(startStuff)
	theatersAndTimes = [(theaterName.strip(), showTimes.strip())]
	
	# some films (those showing at more than one theater!) have extra
	# table rows with 'class="follow"', one for each extra theater
	otherStuff = filmSoup.find_all("tr", {"class": "follow"})
	if len(otherStuff) > 0:
		# more theaters!
		for nextSoup in otherStuff:
			theaterName = GetTheater(nextSoup)
			showTimes = GetShowTimes(nextSoup)
			theatersAndTimes.append((theaterName.strip(), showTimes.strip()))

	return theatersAndTimes


def GetScheduleDates( soup ):
	"""Given a BeautifulSoup object corresponding to the artechock.de web
	page, extract the start and end dates for the current schedule.
	"""
	
	h2 = soup.find_all("h2")
	for h2obj in h2:
		txt = h2obj.getText()
		if txt.find("Filme im Originalton") > -1:
			p = txt.split(":")[1]
			pp = p.split()
			startDate,endDate = pp[1],pp[4]
			return startDate + "-" + endDate
	return None


working_notes = """

# load text-file into BBEdit, convert to UTF-8, save

txtv = open(testTextVersion).read()
soup = BeautifulSoup(txtv)

# extract the table with movie listings (should be only one):
listingsTable = soup.find_all("table", {"class": "linien prog film"})[0]
txtVersion = listingsTable.prettify()
# strip off the final "</table>":
txtVersion = txtVersion.replace("</table>", "")
# split it up into chunks starting with '<tr class="start"', then paste that
# text back onto the beginning of each chunk (skip first chunk, since it's just
# the start of the table
z = txtVersion.split('<tr class="start"')
filmChunks = ['<tr class="start"' + zp for zp in z[1:]]

filmDict = OrderedDict()
titlesEnglish = []
for filmChunk in filmChunks:
	newSoup = BeautifulSoup(filmChunk, "html.parser")
	startBlob = newSoup.find_all("tr", {"class": "start"})[0]
	titleText = startBlob.select("strong")[0].getText()
	pp = titleText.splitlines()
	filmTitle = GetTitle(titleText)
	if titleText.find("(OF)") > -1:
		langType = "OF"
	elif titleText.find("(OmU)") > -1:
		langType = "OmU"
	elif titleText.find("(OmeU)") > -1:
		langType = "OmeU"
	else:
		langType = "German"
	if langType in ["OF", "OmU", "OmeU"]:
		titleText = filmTitle + " [" + langType + "]"
		titlesEnglish.append(titleText)
		filmDict[titleText] = newSoup


outf = open(fdesk+"test_films.txt", 'w')
for title in titlesEnglish:
	theaterTimeList = GetTheatersAndTimes(filmDict[title])
	firstLine = title
	for i in range(len(theaterTimeList)):
		theaterTime = theaterTimeList[0]
		line = "%s: %s" % (theaterTime[0], TranslateTimesSimple(theaterTime))
		if i == 0:
			line = title + ": " + line
		else:
			line = "\t\t" + line
		outf.write(line + "\n")
	outf.write("\n")
outf.close()


"""


def GetSoupObjectFromURL( url=artechockURL ):
	print("Fetching current web page from artechock.de ...")
	# not much point in trying to handle the exception, since sometimes
	# a whole bunch are generated
	res = requests.get(url)
	res.raise_for_status()
	inputText = res.text

	return BeautifulSoup(inputText, parserName)
	
def GetAndProcessFilmListings( input, outputFname, getGermanFilms=False ):
	"""
	Reads HTML produced by artechock.de and saves cleaned-up text file listing
	just those movies labeled as "(OF)", "(OmU)", or "(OmeU)".
	
		input = "url" to specify retrieving the web page from artechock.de
			= path-to-filename to specify reading a saved HTML file
		
		outputFname = filename to save results in; use 'DEFAULT' to specify
			the format "currentfiles_<start_date>-<end_data>.txt"
	"""
	
	if input == "url":
		soup = GetSoupObjectFromURL(artechockURL)
	else:
		inputText = open(input).read()
		soup = BeautifulSoup(inputText, parserName)

	# extract the table with movie listings (should be only one of these):
	listingsTable = soup.find_all("table", {"class": "linien prog film"})[0]
	txtVersion = listingsTable.prettify()
	# strip off the final "</table>":
	txtVersion = txtVersion.replace("</table>", "")
	# split it up into chunks starting with '<tr class="start"', then paste that
	# text back onto the beginning of each chunk (skip first chunk, since it's just
	# the start of the table)
	pieces = txtVersion.split('<tr class="start"')
	filmChunks = ['<tr class="start"' + p for p in pieces[1:]]

	filmDict = OrderedDict()
	titlesNonGerman = []
	for filmChunk in filmChunks:
		newSoup = BeautifulSoup(filmChunk, parserName)
		startBlob = newSoup.find_all("tr", {"class": "start"})[0]
		titleText = startBlob.select("strong")[0].getText()
		pp = titleText.splitlines()
		filmTitle = GetTitle(titleText)
		if titleText.find("3D") > -1:
			filmTitle += " (3D)"
		if titleText.find("(OF)") > -1:
			langType = "OF"
		elif titleText.find("(OmU)") > -1:
			langType = "OmU"
		elif titleText.find("(OmeU)") > -1:
			langType = "OmeU"
		else:
			langType = "German"
		if getGermanFilms or (langType in ["OF", "OmU", "OmeU"]):
			titleText = filmTitle + " [" + langType + "]"
			titlesNonGerman.append(titleText)
			filmDict[titleText] = newSoup

	if outputFname == "DEFAULT":
		scheduleDates = GetScheduleDates(soup)
		if scheduleDates is None:
			print("Unable to extract schedule dates from HTML!")
			outputFname = "currentfilms.txt"
		else:
			outputFname = "currentfilms_{0}.txt".format(scheduleDates)
	outf = open(outputFname, 'w')
	for title in titlesNonGerman:
		theaterTimeList = GetTheatersAndTimes(filmDict[title])
		for i in range(len(theaterTimeList)):
			if i == 0:
				line = title + ":\n"
			else:
				line = ""
			theaterTime = theaterTimeList[i]
			line += "\t%s: %s" % (theaterTime[0], TranslateTimesSimple(theaterTime))
			outf.write(line + "\n")
		outf.write("\n")
	outf.close()


def main(argv=None):

	usageString = "%prog [options] blahblahblah\n"
	parser = optparse.OptionParser(usage=usageString, version="%prog ")


	parser.add_option("-o", "--output", type="str", dest="outputFilename",
					  default=None, help="name for output text file")
	parser.add_option("--input", type="str", dest="inputFilename",
					  default=None, help="read local file (no web retrieval)")
	parser.add_option("--german-films", action="store_true", dest="germanFilms",
					  default=False, help="extract German-language films, too")
	
	(options, args) = parser.parse_args(argv)
	# args[0] = name program was called with
	# args[1] = first actual argument, etc.
	
	if options.outputFilename is None:
		outputFname = "DEFAULT"
	else:
		outputFname = options.outputFilename
	if options.inputFilename is None:
		input = "url"
	else:
		input = options.inputFilename
	
	GetAndProcessFilmListings(input, outputFname, getGermanFilms=options.germanFilms)


if __name__ == '__main__':
	
	main(sys.argv)
