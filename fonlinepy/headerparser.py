import re, ast

"""

	Used to parse C/C++ header files for preprocessor defines.

"""


def parse_header(lines):
	
	define_regex = re.compile(r'\s*\#\s*define\s+([^\s]+)(.*)$')

	is_none = lambda x: not x is None
	
	lines = map(define_regex.match, lines)
	lines = filter(is_none, lines)

	for l in lines:
		def_name = l.group(1)
		def_val = l.group(2)
		def_val = def_val.split("//")[0]
		value = None
		def_val = def_val.strip()
		if len(def_val) == 0:
			value = ""
		else:
			#print (def_val)
			try:
				value = ast.literal_eval(def_val)
			except:
				pass
		yield (def_name, value)

def parse_header_file(server, f):
	import os
	p = os.path.join(server, f)
	for l in parse_header(open(p, errors='ignore')):
		yield l


def get_item_flags(defines):
	"""
		From dictionary of defines (define name -> value)
		get item flags and such
	"""
	import sys
	
	
	# list of things to find and their associated define prefixes.
	# The boolean value is whether the define name should be stripped of the prefix
	dict_pairs = [
		("item_data", "ITEM_DATA_", False),
		("item_events", "ITEM_EVENT_", False),
		("item_perks", "ITEM_PERK_", False),
		("item_types", "ITEM_TYPE_", False),
		("item_flags", "ITEM_", True) #store item flags without the "ITEM_" prefix
	]
	dctt = dict((x, {}) for x, _, _ in dict_pairs)
	for k, v in defines.items():
		for ttype, tprefix, tstrip in dict_pairs:
			
			if k.startswith(tprefix):
				if tstrip:
					k = k[len(tprefix):]
				if v in dctt[ttype]:
					print("Duplicate {} definition for value {} ({} and {}). Ignoring the latter".format(tprefix, v, dctt[ttype][v], k), file=sys.stderr)
					continue
				dctt[ttype][v] = k
				break
	return dctt
	
if __name__ == "__main__":
	import sys
	for m in parse_header(sys.stdin):
		print ("{},{}".format(*m))
