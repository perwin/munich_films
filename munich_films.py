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
# [ ] Generate day-by-dat listings
#
# [ ] Merge 3D and non-3D versions of same film?
#
# [X] Add current date (default) output filename from artechock.de site?
#
#
# Really speculative
# [X] Option to include German-language films
#
# [ ] Create HTML version with links to IMDB pages on films
#

from __future__ import print_function

import sys, optparse, copy, time, re
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


def IsShowtime( string ):
	"""Determines whether string has the format xx:xx, where xx = pair
	of digits.
	"""
	s = string.strip()
	if len(s) == 5 and s[2] == ":" and s[:2].isdigit() and s[3:].isdigit():
		return True
	else:
		return False


# KEEP
def TranslateDays( string ):
	for Tag in TAGEN:
		string = string.replace(Tag, DAYS_TO_ENGLISH[Tag])
	return string

def TranslateTimesSimple( theaterTime ):
	"""Given a tuple of(theaterName, movie showtimes) in German, returns 
	a string with the movie showtimes in English.
	"""
	showtimes = theaterTime[1]
	# strip off extra stuff (some lines have extra spaces and \n)
	showtimesClean = showtimes.splitlines()[0]
	# fix for Wekstattkino entries, which usually end up with "(" at end of line
	if showtimesClean[-1] == "(":
		showtimesClean = showtimesClean[:-1]
	# strip off excess spaces at beginning or end
	showtimesClean = showtimesClean.rstrip()
	showtimesClean = showtimesClean.lstrip()
	# translate to English
	showtimesClean = showtimesClean.replace("tgl.", "daily")
	showtimesClean = showtimesClean.replace(u"außer", "except")
	showtimesClean = showtimesClean.replace("auch", "also")
	showtimesClean = TranslateDays(showtimesClean)
	return showtimesClean
	
	
# KEEP
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
	
	Used in GetTheatersAndTimes.
	"""
	# safest thing is to look for "link" class within "mid b" column
	midCol = soup.find("td", {"class": "mid b"})
	link = midCol.find("span", {"class": "link"})
	return link.getText()
	
def GetShowTimes( soup ):
	"""Given a BeautifulSoup object corresponding to a table row containing
	theater name and showtimes, extract the showtimes.
	
	Used in GetTheatersAndTimes.
	"""
	timesBlob = soup.find_all("td", {"class": "right"})[0]
	# get rid of Unicode non-breaking spaces
	showTimes = timesBlob.getText()
	showTimes = showTimes.replace(u'\xa0', u' ')
	return showTimes
	
def GetTheatersAndTimes( singleFilmSoup ):
	"""Given a BeautifulSoup object corresponding to the set of table rows
	for a given film, extract the theater names and corresponding showtimes.
	
	Returns a list of tuples:
		[(theater1, showtimes1), (theater2, showtimes2), ...]
	
	Sample output:
		[('Museum Lichtspiele',
		  'So. 10:30\n    \n     (\n     \n      artechock-Kritik\n     \n     )')]
	"""
	# all films have at least a "start" table row ('class="start"')
	startStuff = singleFilmSoup.find_all("tr", {"class": "start"})[0]
	theaterName = GetTheater(startStuff)
	showTimes = GetShowTimes(startStuff)
	theatersAndTimes = [(theaterName.strip(), showTimes.strip())]
	
	# some films (those showing at more than one theater!) have extra
	# table rows with 'class="follow"', one for each extra theater
	otherStuff = singleFilmSoup.find_all("tr", {"class": "follow"})
	if len(otherStuff) > 0:
		# more theaters!
		for nextSoup in otherStuff:
			theaterName = GetTheater(nextSoup)
			showTimes = GetShowTimes(nextSoup)
			theatersAndTimes.append((theaterName.strip(), showTimes.strip()))

	return theatersAndTimes


# KEEP
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




# KEEP
def GetSoupObjectFromURL( url=artechockURL ):
	print("Fetching current web page from artechock.de ...")
	# not much point in trying to handle the exception, since sometimes
	# a whole bunch are generated
	res = requests.get(url)
	res.raise_for_status()
	inputText = res.text

	return BeautifulSoup(inputText, parserName)


# KEEP
def GetFilmSoupDict( soup, getGermanFilms=False  ):
	"""
	Given a BeautifulSoup object corresponding to the artechock.de web page,
	this function returns a dictionary mapping film names to corresponding
	BeautifulSoup objects (i.e., from the subset of the web page dealing with
	an individual film).
	"""
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
	filmTitles = []
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
			filmTitles.append(titleText)
			filmDict[titleText] = newSoup

	return filmDict, filmTitles


# [ ] POSSIBLE NEW APPROACH:
# Filter filmTextDict once for each day --> 7 reduced filmTextDict instances, each
# one containing only those theater+showtimes which apply to the day in question.
# Then, for output, select the reduced dict for the requested day; only print the
# entries with non-null showtimes.

def RemoveDaysFromShowtime( showtimeString ):
	"""
	Given a showtime string of the form "M 20:00, 23:00" or "Sat/Sun 20:00", this function
	removes *all* the days, returning just the time(s).
	"""
	s = showtimeString.strip()
	pp = s.split()
	dayString = pp[0]
	return s.lstrip(dayString).strip()


dailyPatterns = """
daily 23:10
daily 16:40, 19:50, 22:50
daily 19:00 (Sun 19:30)
daily 15:00, 17:45, 20:30 (except M)
daily 16:20 (except Fr.), 18:35
daily except Tu 22:55
daily except Sat/Tu 21:30
daily except W 19:10; Sat/Sun also 15:30; Tu also 13:00
daily except W 16:10, 22:15; Sun also 11:00
daily except M 18:30; M 18:00
daily except Sat/Sun 15:15; Sat/Sun 13:00
"""

paranthesizedAlsos = """
daily except W 16:10, 22:15; Sun also 11:00
daily except W 19:10; Sat/Sun also 15:30; Tu also 13:00
"""

findParenthesizedText = re.compile("\((?P<text>\D+\s+\S+)\)")
findParenthesizedExceptDay = re.compile("\(except\s+(?P<days>\S+)\)")
findAlsoText = re.compile("(?P<days>\D+) also (?P<time>\S+)")

def IsValidDay( showTime, day ):
	"""Given a showTime string possibly containing "(except <days>)", returns
	True if day is *not* in the exception list.
		forms for showTime: "20:00", "16:20 (except Sun)", etc.
	"""
	m = findParenthesizedExceptDay.search(showTime)
	if m is None:
		return True
	else:
		exceptionDays = m.group("days")
		if day in exceptionDays:
			return False
		else:
			return True

	
# [ ] Currently being tested
def ExtractDailyTimes( showtimeBlock, day ):
	"""Code designed to process the different forms of "daily xxx" showtimes.
	Given an input "daily xxx" segment of text and a specified day, this
	function returns the corresponding string of showtimes for that day.
		Examples:
			ExtractDailyTimes("daily 16:40, 19:50, 22:50", "<anyday>") --> "16:40, 19:50, 22:50"
			ExtractDailyTimes("daily 19:00 (Sun 19:30)", "Sun") --> "19:30"
	"""
	s = showtimeBlock.lstrip("daily ")
	# TODO: look for "also" text, save if matches day
	if s.find("except") < 0:
		# no "except" text, so things are simpler
		m = findParenthesizedText.search(s)
		if m is None:
			validTimeString = s.split("(")[0].strip()
		else:
			# possible alternate time for this day?
			altTimeText = m.group("text")
			if altTimeText.find(day) > -1:
				pp = altTimeText.split()
				validTimeString = altTimeText.lstrip(pp[0]).strip()
			else:
				validTimeString = s.split("(")[0].strip()
	else:
		# process "except"
		pp = s.split()
		m = findParenthesizedExceptDay.search(s)
		if m is None:
			# assume that pattern is "daily except ..."
			invalidDays = pp[1]
			if invalidDays.find(day) > -1:
				validTimeString = None
			else:
				validTimeString = s.lstrip(pp[0] + " " + pp[1])
		else:
			# OK we have a list of times with "(except <days>)", so at least *some* of the
			# times are valid for this day
			validTimes = [ time.split("(")[0].strip() for time in s.split(",") if IsValidDay(time, day) ]
			if len(validTimes) == 1:
				validTimeString = validTimes[0]
			else:
				validTimeString = ", ".join(validTimes)

	return validTimeString
			
		

def GetTimesForOneDay( timesList, day ):
	"""
	IN PROGRESS!  [currently can't handle really complicated film times]
	Returns a list of "theater: times" strings for the film specified by the input
	list of theaters and showtimes, *if* the times include the specified day.
	
	Sample input: ['Mathäser: Sun 11:00 (mit Pause)', 'Cinemaxx: Th 19:30; Sun 16:00']
	Sample output (for case of day = "Sun"): ["Mathäser: 11:00", "Cinemaxx: 16:00"]
	"""
	nTheaters = len(timesList)
	timesForThisDay = []
	for i in range(nTheaters):
		theaterTimesString = timesList[i]
		theaterName = theaterTimesString.split(":")[0]
		# extract just the actual showtimes (chop off the theater name)
		timesString = theaterTimesString.split(theaterName + ":")[1]
		times = timesString.split(";")
		for showtimeBlock in times:
			# iterate over "blocks" (text separated by ";")
			if showtimeBlock.find("daily") > -1:
				validTimesForThisDay = ExtractDailyTimes(showtimeBlock, day)
				if validTimesForThisDay is not None:
					timesForThisDay.append(theaterName + ": " + validTimesForThisDay)
			else:
				showtimeBlockTrimmed = showtimeBlock.split("(")[0]
				if showtimeBlockTrimmed.find(day) > -1:
					validTimesForThisDay = RemoveDaysFromShowtime(showtimeBlockTrimmed)
					timesForThisDay.append(theaterName + ": " + validTimesForThisDay)
		
# 		timesString = timesString.split("(")[0]
# 		if timesString.find("daily") > 0:
# 			timesString = timesString.lstrip("daily ")
# 			timesForThisDay.append(theaterName + ": " + timesString.strip())
# 		else:
# 			times = timesString.split(";")
# 			for showtimeOneDay in times:
# 				if showtimeOneDay.find(day) > -1:
# 					showtimeOneDay = RemoveDaysFromShowtime(showtimeOneDay)
# 					timesForThisDay.append(theaterName + ": " + showtimeOneDay)
			
	return timesForThisDay
	
				

# KEEP
def MakeFilmTextDict( filmSoupDict, titles ):
	"""
	Given a dict mapping film titles to Beautiful Soup objects derived from the
	HTML for individual films (i.e., output of GetFilmSoupDict) and a list of
	the film titles, this function returns a dict mapping film names to lists of 
	theater+showtimes strings. E.g.,
	
		filmTextDict['The Boss [OF]'] = ['Mathäser: Sun 11:00 (mit Pause)', 
										'Cinemaxx: Th 19:30; Sun 16:00']
	"""
	newDict = {}
	for title in titles:
		theaterTimeList = GetTheatersAndTimes(filmSoupDict[title])
		timesList = []
		for i in range(len(theaterTimeList)):
			theaterTime = theaterTimeList[i]
			line = "%s: %s" % (theaterTime[0], TranslateTimesSimple(theaterTime))
			timesList.append(line)
		newDict[title] = timesList
	return newDict
	
	
# KEEP
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
		with open(input) as f:
			inputText = f.read()
			soup = BeautifulSoup(inputText, parserName)

	filmSoupDict, filmTitles = GetFilmSoupDict(soup, getGermanFilms)
	filmTextDict = MakeFilmTextDict(filmSoupDict, filmTitles)
	
	if outputFname == "DEFAULT":
		scheduleDates = GetScheduleDates(soup)
		if scheduleDates is None:
			print("Unable to extract schedule dates from HTML!")
			outputFname = "currentfilms.txt"
		else:
			outputFname = "currentfilms_{0}.txt".format(scheduleDates)
	with open(outputFname, 'w') as outf:
		for title in filmTitles:
			timesList = filmTextDict[title]
			for i in range(len(timesList)):
				if i == 0:
					line = title + ":\n"
				else:
					line = ""
				line += "\t%s" % timesList[i]
				outf.write(line + "\n")
			outf.write("\n")
	print("Saved current film schedule in \"{0}\".".format(outputFname))


def main(argv=None):

	usageString = "%prog [options] blahblahblah\n"
	parser = optparse.OptionParser(usage=usageString, version="%prog ")


	parser.add_option("-o", "--output", type="str", dest="outputFilename",
					  default=None, help="name for output text file [default = \"currentfilms_dd.mm.yyyy-dd.mm.yyy\"]")
	parser.add_option("--input", type="str", dest="inputFilename",
					  default=None, help="read local HTML file instead of web retrieval [for testing purposes]")
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
