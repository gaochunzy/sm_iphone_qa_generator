# SMGenerator.py

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

def main():
	if len(sys.argv) != 3:
		print "Usage: python SMGenerato.py YOUR_FILE'S_NAME OUTPUT_FILE_NAME"
	db = sqlite3.connect("app.db")
	cursor = db.cursor()

	word_file = open(sys.argv[1])
	output = open(sys.argv[2], mode='w')
	unrcg = open("unrecognized.txt", mode='a')

	while True:
		line = word_file.readline()
		if not line: break
		if line.strip() == "": continue
		word = line.split()[0]
	
		cursor.execute("SELECT entry FROM entries WHERE word = \"" + word + "\" OR lower_word =\"" + word + "\"")
		stuff = cursor.fetchall()
		if len(stuff) < 1: 
			print "Can't find: " + word
			unrcg.write(word + "\n")			
			continue
		
		result = stuff[0][0]
	
		if result == None: continue

		Answer = "";
		Question = "";
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
					Answer = Answer + '<font face="' + ENTRY_INDEX_FONT + '" size="' + ENTRY_INDEX_SIZE + '">' + str(entry_index) + '. </font>'
					entry_index = entry_index + 1

				definitions = entry.findall('d')
				if len(definitions) > 0:
					for definition in definitions:
						if definition != None and definition.text != None:	
							Answer = Answer + '<font face="' + DEFINITION_FONT + '">' + definition.text + ' </font>'

				examples = entry.findall('ex')
				if examples != None: 
					example_tag = 0
					for example in examples:
						if example_tag == 0:
							example_tag = 1
						else:
							Answer = Answer + " | "
						
						Answer = Answer + '<font face="' + EXAMPLE_FONT + '" size="' + EXAMPLE_SIZE + '">' +  re.sub("[^<]*<ex>(.*)</ex>.*", "\\1",tostring(example)) + '</font>'

					Answer = Answer + '<br/>'
				
				special_use = entry.findall('specUse')
				if special_use != None:
					for spec in special_use:
						cases = spec.findall('MS')
						if cases != None:
							for case in cases:
								Answer = Answer + SPECIAL_USE_INDICATOR + " "
								spec_defs = case.findall('d')
								if spec_defs != None:
									for spec_def in spec_defs:
										if spec_def != None and spec_def.text != None:
											Answer = Answer + spec_def.text

								spec_examples = case.findall('ex')
								if spec_examples != None:
									spec_example_tag = 0

									for spec_example in spec_examples:
										if spec_example_tag == 0:
											spec_example_tag = 1
										else:
											Answer = Answer + " | "

										Answer = Answer + '<font face="' + EXAMPLE_FONT + '" size="' + EXAMPLE_SIZE + '">' + re.sub("[^<]*<ex>(.*)</ex>.*", "\\1", tostring(spec_example)) + '</font>'
								Answer = Answer + '<br/>'
				
				Answer = Answer + '<hr/>'
		Question = '<font face="' + QUESTION_FONT + '" size="' + QUESTION_SIZE + '">' + word + "</font>"

		head = dom.findall('h')
		if len(head) > 0:
			pg = head[0].findall("pg")
			if len(pg) > 0:
				pr = pg[0].findall("pr")
				if len(pr) > 0 and pr != None and pr[0] != None and pr[0].text != None:
					pronunciation = '<font face="' + PHONETIC_SYMBOL_FONT + '" size="' + PHONETIC_SYMBOL_SIZE + '" color="' + PHONETIC_SYMBOL_COLOR + '">' + pr[0].text + "</font>";
				else: 
					pronunciation = ""
			else:
				pronunciation = ""
		else:
			pronunciation = ""
		
		out_text = "Q: " + Question + " |" + pronunciation + "|" +  "\n" + "A: " + Answer + "\n\n"
		output.write(out_text.encode('utf8'))

	output.close()
	db.close()
if __name__ == "__main__":
	main()
