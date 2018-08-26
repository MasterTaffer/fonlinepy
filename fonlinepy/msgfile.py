import re


"""
	Parses Fallout MSG files

	If run as stand-alone script, will read data from stdin and output the
	MSG data enclosed in double quotes in CSV format.
"""

def msg_reader(data, line_index=None, file_name=None):
	last_msg = None
	last_msg_index = 0
	if line_index is None:
		line_index = 0

	def warn():
		if filename:
			logging.warning("Invalid MSG data at line %s in file %s", line_index + 1, file_name)
		else:
			logging.warning("Invalid MSG data at line %s", line_index + 1)
	
	msg_re = re.compile(r'^\s*\{')
	msg_secs_re = re.compile(r'^\s*\{([^}]*)\}\s*\{([^}]*)\}\s*\{([^}]*)\}\s*(\#.*)?$')

	line_index -= 1
	while True:
		line_index += 1
		l = next(data)
		if not l:
			if last_msg:
				warn()
			return
		if last_msg is None:
			last_msg_index = line_index
			if len(l) == 0:
				continue
			if msg_re.match(l):
				last_msg = l
			else:
				l = l.strip()
				if len(l) == 0:
					continue

				if l[0] == '#':
					continue

				warn()
				continue
		else:
			last_msg = last_msg + l

		endcnt = last_msg.count("}")
		if endcnt > 3:
			warn()
			last_msg = None
		if endcnt == 3:
			last_msg = last_msg.replace('\n','')
			match = msg_secs_re.match(last_msg)
			if not match:
				warn()
				last_msg = None
				continue
			msg_data = [match.group(1), match.group(2), match.group(3)]
			line_range = (last_msg_index, line_index + 1)
			last_msg = None
			yield (msg_data, line_range)

if __name__ == "__main__":
	import sys
	for m in msg_reader(sys.stdin, line_index=0, file_name="stdin"):
		print ("\"{}\",\"{}\",\"{}\"".format(*map(lambda x: x.replace("\"", "\"\""), m[0])))