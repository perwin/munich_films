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


# possible output from munich_films.munich_films.MakeFilmTextDict
title1 = 'Le amiche (Die Freundinnen) [OmeU]'
timesList1 = ['Werkstattkino: M 20:00']
dayAndTimes1 = [[], ["Werkstattkino: M 20:00"], [], [], [], [], []]

title10 = 'Captain America: Civil War (The First Avenger: Civil War) [OF]'
timesList10 = ['Cinema: Th 22:05; Sat 12:35', 'Mathäser: Th/M/W 16:45',
 'Museum Lichtspiele: daily 16:40, 19:50, 22:50']
dayAndTimes10 = [["Museum Lichtspiele: 16:40, 19:50, 22:50"], 
	["Mathäser: Th/M/W 16:45", "Museum Lichtspiele: 16:40, 19:50, 22:50"],
	["Museum Lichtspiele: 16:40, 19:50, 22:50"],
	["Mathäser: Th/M/W 16:45", "Museum Lichtspiele: 16:40, 19:50, 22:50"],
	["Cinema: Th 22:05", "Mathäser: Th/M/W 16:45", "Museum Lichtspiele: 16:40, 19:50, 22:50"],
	["Museum Lichtspiele: 16:40, 19:50, 22:50"],
	["Cinema: Sat 12:35","Museum Lichtspiele: 16:40, 19:50, 22:50"]]
 


# tests for a single function

class munich_filmsCheck(unittest.TestCase):
	def setUp(self):
		# do any setup
		if os.path.exists(TEMP_OUTPUT):
			os.remove(TEMP_OUTPUT)
	
	# REMINDER: names of methods *must* begin with "test", otherwise they won't
	# be recognized!
	
	def testGetTimesForOneDay(self):
		# setup: create input and reference
		input = timesList1
		correct = dayAndTimes1
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.GetTimesForOneDay(input, inputDay))
		self.assertEqual(correct, result)

		input = timesList10
		correct = dayAndTimes10
		result = []
		for inputDay in ["Sun", "M", "Tu", "W", "Th", "F", "Sat"]:
			result.append(munich_films.GetTimesForOneDay(input, inputDay))
		self.assertEqual(correct, result)




if __name__	== "__main__":
	
	print("** Unit tests for munich_films.py **")
	unittest.main()	  
