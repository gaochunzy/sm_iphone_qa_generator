#!/usr/bin/python
# SMGenerator.py

import time
import re
import sys
import sqlite3
from xml.etree.ElementTree import fromstring, tostring

QUESTION_FONT = 'Palatino-Bold'
QUESTION_SIZE = '5'
PHONETIC_SYMBOL_SIZE = '4'
PHONETIC_SYMBOL_FONT = 'Palatino-Bold'
PHONETIC_SYMBOL_COLOR = "Gray"
DEFINITION_FONT = "Georgia"
EXAMPLE_FONT = "Baskerville-Italic"
EXAMPLE_SIZE = "4";
ENTRY_INDEX_FONT = "Courier-Bold"
ENTRY_INDEX_SIZE = "4"

SPECIAL_USE_INDICATOR = u'\u2023'

#global variables about running status and others
global db
global cursor
global DEBUG 
global VERBOSE

DEBUG=False
VERBOSE=False

# parse command line options and set specific global variables
def parse_command_line_option(argument):
	global VERBOSE
	for option in range(1, len(argument)):
		if argument[option] == 'v':
			VERBOSE=True
		elif argument[option] == 'h':
			help()
			return False
		else:
			print "Unknown option '" + argument[option] + "'"
			return False
	return True

# return files specified in command line
# every arguments start with '-' is considered as an option
def count_IO_files():
	count = 0
	for arg in range(1, len(sys.argv)):
		if(sys.argv[arg][0] != '-'):
			count += 1
	return count
	
def help():
	print "Usage:  python SMGenerator.py INPUT_FILE [OUTPUT_FILE]"
	print "        INPUT_FILE is the file where you put your words in."
	print "        OUTPUT_FILE(optional) is the file that store all the output."
	print "Option: -v: display extra information where processing"
	print "        -h: display this help"
	
def input_file_index():
	for index in range(1, len(sys.argv)):
		if(sys.argv[index][0] != '-'):
			return index
	return -1

def output_file_index():
	input_file_hit = False

	for index in range(1, len(sys.argv)):
		if(sys.argv[index][0] != '-'):
			if input_file_hit == False:
				input_file_hit = True
			else:
				return index
	return -1


def parse_definition(definitions):
	definition_text = ""
	stack = []
	status = "NORMAL"

	for definition in definitions:
		print tostring(definition),
		if re.match("[^<]*<d>[^<]*<xrefGrp>[^<]*<xref[^>]*>[^<]*<x>[^<]*</x>[^<]*</xref>[^<]*</xrefGrp>[^<]*</d>.*", tostring(definition)):
			xrefWord = re.sub("[^<]*<d>[^<]*<xrefGrp>[^<]*<xref[^>]*>[^<]*<x>([^<]*)</x>[^<]*</xref>[^<]*</xrefGrp>[^<]*</d>.*","\\1", tostring(definition));
			xrefText = parse_entry(xrefWord)
			if xrefText != None:
				stack.append(xrefText)
				status = "CROSSREF"

		if definition != None and definition.text != None:	
			definition_text = definition_text + '<font face="' + DEFINITION_FONT \
			+ '">' + definition.text + ' </font>'

	return (status,definition_text, stack)


def parse_example(examples):
	example_text = ""
	example_tag = 0

	for example in examples:
		if example_tag == 0:
			example_tag = 1
		else:
			example_text = example_text + " | "
		
		example_text = example_text + '<font face="' + EXAMPLE_FONT \
		+ '" size="' + EXAMPLE_SIZE + '">'\
		+ re.sub("[^<]*<ex>(.*)</ex>.*", "\\1",tostring(example)) + '</font>'
	
	return example_text


def parse_special_use(special_use):
	special_use_text = ""

	for spec in special_use:
		cases = spec.findall('MS')
		if cases != None:
			for case in cases:
				if re.match('<MS core="no">.*((<d>.*</d>)|(<ex>.*</ex>)).*</MS>', tostring(case)):
					special_use_text = special_use_text + SPECIAL_USE_INDICATOR + " "
					spec_defs = case.findall('d')
					if spec_defs != None:
						for spec_def in spec_defs:
							if spec_def != None and spec_def.text != None:
								special_use_text = special_use_text + spec_def.text

					spec_examples = case.findall('ex')
					if spec_examples != None:
						spec_example_tag = 0

						for spec_example in spec_examples:
							if spec_example_tag == 0:
								spec_example_tag = 1
							else:
								special_use_text = special_use_text + " | "

							spec_example_text = re.sub("[^<]*<ex>(.*)</ex>.*", "\\1", \
										tostring(spec_example)) 
							special_use_text = special_use_text + '<font face="' + EXAMPLE_FONT \
							+ '" size="' + EXAMPLE_SIZE + '">' \
							+ spec_example_text \
							+ '</font>'
					special_use_text = special_use_text + '<br/>'

	return special_use_text

	
def parse_entry_head(head):
	pronunciation = ""

	pg = head[0].findall("pg")
	if len(pg) > 0:
		pr = pg[0].findall("pr")
		if len(pr) > 0 and pr != None and pr[0] != None and pr[0].text != None:
			pronunciation_text = re.sub("[^<]*<pr>(.*)</pr>.*", "\\1", tostring(pr[0]))
			pronunciation = '<font face="' + PHONETIC_SYMBOL_FONT + '" size="' + PHONETIC_SYMBOL_SIZE \
			+ '" color="' + PHONETIC_SYMBOL_COLOR + '">' + pronunciation_text + "</font>"

	return pronunciation


def parse_entry(word):
	global db
	global cursor

	global unrcg

	entry_text = ""

	if VERBOSE:
		print '[SMG] Fetching "'+ word+'".'

	cursor.execute("SELECT entry FROM entries WHERE word = \"" \
	+ word + "\" OR lower_word =\"" + word + "\"")

	stuff = cursor.fetchall()
	if len(stuff) < 1: 
		print "[SMG] Can't find: " + word
		unrcg.write(word + "\n")			
		return	
	
	result = stuff[0][0]

	if result == None: return

	Answer = "";
	Question = "";
	ps = None
	pl = None
	cross_reference_stack = []

	dom = fromstring(result)
	for part_of_speech in dom.findall('sb'):
		pl = part_of_speech.find('pl')
		if pl != None: ps = pl.find('ps')
		if ps != None: Answer = Answer + ps.text + "<br/>"

		entries = part_of_speech.findall('se')
		if len(entries) < 2:
			entry_index = 0
		else:
			entry_index = 1

		for entry in entries:
			if entry_index > 0:
				Answer = Answer + '<font face="' + ENTRY_INDEX_FONT \
				+ '" size="' + ENTRY_INDEX_SIZE + '">' + str(entry_index) + '. </font>'
				entry_index = entry_index + 1

			definitions = entry.findall('d')
			if len(definitions) > 0:
				parsed_text = parse_definition(definitions)
				if parsed_text[0] == "NORMAL":
					definition_text = parsed_text[1] 
					if definition_text.strip() != "":
						Answer = Answer + definition_text
				elif parsed_text[0] == "CROSSREF":
					print "HIT",
					while len(parsed_text[2]) > 0:
						cross_reference_stack.append(parsed_text[2].pop())

			examples = entry.findall('ex')
			if len(examples) > 0: 
				example_text = parse_example(examples)
				if example_text.strip() != "":
					Answer = Answer + example_text

			Answer = Answer + '<br/>'
			
			special_use = entry.findall('specUse')
			if special_use != None:
				special_use_text = parse_special_use(special_use)
				if special_use_text.strip() != "":
					Answer = Answer + special_use_text
			
			Answer = Answer + '<hr/>'
	Question = '<font face="' + QUESTION_FONT + '" size="' + QUESTION_SIZE + '">' + word + "</font>"

	head = dom.findall('h')
	pronunciation =""
	if len(head) > 0:
		pronunciation = parse_entry_head(head)		
	
	while len(cross_reference_stack) > 0:
		cross_ref_item = cross_reference_stack.pop()
		Answer = Answer + cross_ref_item[0] + " |" + cross_ref_item[1] + "|" +  "\n" + cross_ref_item[2] + "\n"
	return (Question, pronunciation, Answer)
	

def main():
	global VERBOSE
	global db
	global cursor

	global unrcg

	# detect command line options
	for argument_index in range(1, len(sys.argv)):
		if sys.argv[argument_index][0] == '-':
			# exit if parsing failed
			if parse_command_line_option(sys.argv[argument_index]) != True:
				sys.exit()
	
	# check whether input/output files are correctly specified.
	number_of_files = count_IO_files();
	if number_of_files < 1 or number_of_files > 2:
		help()
		sys.exit()
	
	if VERBOSE == True:	
		print "[SMG] Total", number_of_files, "file(s)"

	db = sqlite3.connect("app.db")
	cursor = db.cursor()

	# open input file
	word_file = open(sys.argv[input_file_index()])

	# if output file is specified, create it, or generate a output name with current time.
	if number_of_files == 2:
		output = open(sys.argv[output_file_index()], mode='w')
	else:
		output = open('SMGenerator-' + time.strftime('%Y-%m-%d-%H-%M-%S') + '.txt', mode='w')

	# open the file and put all unrecognized word in it.
	# It's a temporary way.. I will take some way neater...
	unrecognize_word_file = "unrecognized.txt"
	unrcg = open(unrecognize_word_file, mode='a')

	if VERBOSE == True:
		print "[SMG] Input file: ", word_file.name
		print "[SMG] Output file:", output.name
		print "[SMG] Unrecognized words will be put in", unrcg.name

	while True:
		line = word_file.readline()
		if not line: break
		if line.strip() == "": continue
		word = line.split()[0]
		entry_text = parse_entry(word)
		
		if entry_text != None:
			out_text = "Q: " + entry_text[0] + " |" + entry_text[1] + "|" +  "\n" + "A: " + entry_text[2] + "\n\n"
			if out_text.strip() != "":	
				output.write(out_text.encode('utf8'))

	output.close()
	db.close()
if __name__ == "__main__":
	main()
