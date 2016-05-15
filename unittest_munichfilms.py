#!/usr/bin/env python3

# Simple template for doing unit tests

"""Unit test for munich_films.py"""

import os, time
import unittest
import requests
from bs4 import BeautifulSoup
import munich_films   # module to be tested

# prepare input and reference data
testTextVersion = "artechok_originalton.html"

REFERENCE_OUTPUT = "reference_output.txt"
TEMP_OUTPUT = "temp_output.txt"


# "daily" patterns
dailyText1 = "daily 23:10"
correctDaily1 = ["23:10"]*7
dailyText2 = "daily 16:40, 19:50, 22:50"
correctDaily2 = ["16:40, 19:50, 22:50"]*7
dailyText3 = "daily 19:00 (Sun 19:30)"
correctDaily3 = ["19:30"] + ["19:00"]*6
dailyText4 = "daily 15:00, 17:45, 20:30 (except M)"
correctDaily4 = ["15:00, 17:45, 20:30"] + ["15:00, 17:45"] + ["15:00, 17:45, 20:30"]*5
dailyText5 = "daily except Tu 22:55"
correctDaily5 = ["22:55"]*2 + [None] + ["22:55"]*4
dailyText6 = "daily except Sat/Tu 21:30"
correctDaily6 = ["21:30"]*2 + [None] + ["21:30"]*3 + [None]
dailyText7 = "daily except M 18:30"
correctDaily7 = ["18:30", None] + ["18:30"]*5
dailyText8 = "daily 16:20 (except Fr.), 18:35"
correctDaily8 = ["16:20, 18:35"]*5 + ["18:35"] + ["16:20, 18:35"]
dailyText9 = "daily except W 19:10; Sat/Sun also 15:30; Tu also 13:00"
correctDaily9 = ["15:30, 19:10", "19:10", "13:00, 19:10", None, "19:10", "19:10", "15:30, 19:10"]
dailyText10 = "daily except W 16:10, 22:15; Sun also 11:00"
correctDaily10 = ["11:00, 16:10, 22:15"] + ["16:10, 22:15"]*2 + [None] + ["16:10, 22:15"]*3
dailyText11 = "daily except M 18:30; M 18:00"
correctDaily11 = ["18:30", "18:00", "18:30", "18:30", "18:30", "18:30", "18:30"]
dailyText12 = "daily except Sat/Sun 15:15; Sat/Sun 13:00"
correctDaily12 = ["13:00"] + ["15:15"]*5 + ["13:00"]


# possible output from munich_films.munich_films.MakeFilmTextDict
title1 = 'Le amiche (Die Freundinnen) [OmeU]'
timesList1 = ['Werkstattkino: M 20:00']
dayAndTimes1 = [[], ["Werkstattkino: 20:00"], [], [], [], [], []]

title2 = "L'avventura (Die mit der Liebe spielen) [OmeU]"
timesList2 = ['Werkstattkino: Sat/Sun 20:00']
dayAndTimes2 = [["Werkstattkino: 20:00"], [], [], [], [], [], ["Werkstattkino: 20:00"]]

title3 = "Bahubali: The Beginning [OmU]"
timesList3 = ['Mathäser: Sun 11:00 (mit Pause)', 'Cinemaxx: Th 19:30; Sun 16:00']
dayAndTimes3 = [['Mathäser: 11:00', 'Cinemaxx: 16:00'],
				[], [], [], ['Cinemaxx: 19:30'], [], []]

title4 = "Banshun (Später Frühling) [OmeU]"
timesList4 = ['Filmmuseum München: Sun 21:00; W 18:30 (+Vorfilm »Drei Minuten in einem Film von Ozu«)']
dayAndTimes4 = [['Filmmuseum München: 21:00'], [], [], ['Filmmuseum München: 18:30'],
				[], [], []]

title5 = "Batman v Superman: Dawn of Justice [OF]"
timesList5 = ['Museum Lichtspiele: daily except Tu 22:55']
dayAndTimes5 = [['Museum Lichtspiele: 22:55'], ['Museum Lichtspiele: 22:55'], [],
				['Museum Lichtspiele: 22:55'], ['Museum Lichtspiele: 22:55'], 
				['Museum Lichtspiele: 22:55'], ['Museum Lichtspiele: 22:55']]

title10 = 'Captain America: Civil War (The First Avenger: Civil War) [OF]'
timesList10 = ['Cinema: Th 22:05; Sat 12:35', 'Mathäser: Th/M/W 16:45',
 'Museum Lichtspiele: daily 16:40, 19:50, 22:50']
dayAndTimes10 = [["Museum Lichtspiele: 16:40, 19:50, 22:50"], 
	["Mathäser: 16:45", "Museum Lichtspiele: 16:40, 19:50, 22:50"],
	["Museum Lichtspiele: 16:40, 19:50, 22:50"],
	["Mathäser: 16:45", "Museum Lichtspiele: 16:40, 19:50, 22:50"],
	["Cinema: 22:05", "Mathäser: 16:45", "Museum Lichtspiele: 16:40, 19:50, 22:50"],
	["Museum Lichtspiele: 16:40, 19:50, 22:50"],
	["Cinema: 12:35","Museum Lichtspiele: 16:40, 19:50, 22:50"]]

title11 = 'Captain America: Civil War (The First Avenger: Civil War) (3D) [OF]'
timesList11 = ['Cinema: Th/Sun 15:30, 18:45; Fr. 16:15, 19:30, 22:45; Sat 9:45, 15:45, 21:45; Sun also 22:00; M 18:30, 21:45; Tu 16:00, 19:00, 22:15; W 19:15, 22:30',
 'Gloria: Sun 21:00',
 'Mathäser: Th/Sun/Tu/W 20:00; Fr./Sat 23:00; W also 22:45']
dayAndTimes11 = [["Cinema: 15:30, 22:00", "Gloria: 21:00", "Mathäser: 20:00"], 
	["Cinema: 18:30, 21:45"], ["Cinema: 16:00, 19:00, 22:15", "Mathäser: 20:00"], 
	["Cinema: 19:15, 22:30", "Mathäser: 20:00, 22:45"], 
	["Cinema: 15:30, 18:45", "Mathäser: 20:00"], 
	["Cinema: 16:15, 19:30, 22:45", "Mathäser: 23:00"], 
	["Cinema: 9:45, 15:45, 21:45", "Mathäser: 23:00"]]



# tests for a single function

class munich_filmsCheck(unittest.TestCase):
	def setUp(self):
		# do any setup
		if os.path.exists(TEMP_OUTPUT):
			os.remove(TEMP_OUTPUT)
	
	# REMINDER: names of methods *must* begin with "test", otherwise they won't
	# be recognized!
	
	def testRemoveDaysFromShowtime(self):
		inputList = ['M 20:00', 'Sat/Sun 20:00']
		correct = ['20:00', '20:00']
		result = []
		for input in inputList:
			result.append(munich_films.RemoveDaysFromShowtime(input))
		self.assertEqual(correct, result)
	
	
	def testExtractDailyTimes1(self):
		input = dailyText1
		correct = correctDaily1
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.ExtractDailyTimes(input, inputDay))
		self.assertEqual(correct, result)

	def testExtractDailyTimes2(self):
		input = dailyText2
		correct = correctDaily2
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.ExtractDailyTimes(input, inputDay))
		self.assertEqual(correct, result)

	def testExtractDailyTimes3(self):
		input = dailyText3
		correct = correctDaily3
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.ExtractDailyTimes(input, inputDay))
		self.assertEqual(correct, result)

	def testExtractDailyTimes4(self):
		input = dailyText4
		correct = correctDaily4
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.ExtractDailyTimes(input, inputDay))
		self.assertEqual(correct, result)

	def testExtractDailyTimes5(self):
		input = dailyText5
		correct = correctDaily5
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.ExtractDailyTimes(input, inputDay))
		self.assertEqual(correct, result)
	
	def testExtractDailyTimes6(self):
		input = dailyText6
		correct = correctDaily6
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.ExtractDailyTimes(input, inputDay))
		self.assertEqual(correct, result)

	def testExtractDailyTimes7(self):
		input = dailyText7
		correct = correctDaily7
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.ExtractDailyTimes(input, inputDay))
		self.assertEqual(correct, result)

	def testExtractDailyTimes8(self):
		input = dailyText8
		correct = correctDaily8
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.ExtractDailyTimes(input, inputDay))
		self.assertEqual(correct, result)

	def testExtractDailyTimes9(self):
		input = dailyText9
		correct = correctDaily9
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.ExtractDailyTimes(input, inputDay))
		self.assertEqual(correct, result)
	
		
# 	def testGetTimesForOneDay(self):
# 		# setup: create input and reference
# 		input = timesList1
# 		correct = dayAndTimes1
# 		result = []
# 		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
# 			result.append(munich_films.GetTimesForOneDay(input, inputDay))
# 		self.assertEqual(correct, result)
# 
# 		input = timesList2
# 		correct = dayAndTimes2
# 		result = []
# 		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
# 			result.append(munich_films.GetTimesForOneDay(input, inputDay))
# 		self.assertEqual(correct, result)
# 
# 		input = timesList3
# 		correct = dayAndTimes3
# 		result = []
# 		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
# 			result.append(munich_films.GetTimesForOneDay(input, inputDay))
# 		self.assertEqual(correct, result)
# 
# 		input = timesList4
# 		correct = dayAndTimes4
# 		result = []
# 		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
# 			result.append(munich_films.GetTimesForOneDay(input, inputDay))
# 		self.assertEqual(correct, result)
# 
# 		input = timesList5
# 		correct = dayAndTimes5
# 		result = []
# 		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
# 			result.append(munich_films.GetTimesForOneDay(input, inputDay))
# 		self.assertEqual(correct, result)
# 
# 		input = timesList10
# 		correct = dayAndTimes10
# 		result = []
# 		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
# 			result.append(munich_films.GetTimesForOneDay(input, inputDay))
# 		self.assertEqual(correct, result)
# 
# 		input = timesList11
# 		correct = dayAndTimes11
# 		result = []
# 		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
# 			result.append(munich_films.GetTimesForOneDay(input, inputDay))
# 		self.assertEqual(correct, result)
# 



if __name__	== "__main__":
	
	print("** Unit tests for munich_films.py **")
	unittest.main()	  
