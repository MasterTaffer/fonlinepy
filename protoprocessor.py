import fonlinepy.protofile as protofile
import fonlinepy.headerparser as headerparser
import fonlinepy.server as server
import re

"""
	Preprocesses fopro files using macros. All files from input folder are processed.
	Output protos are written in folder defined by --output argument.
	If flag --reverse is specified, the tool expands certain proto fields into 'macros'.
	
	List of macros:
	
	- $def DEFINE_NAME
		Substitutes value field with the value of preprocessor define
		DEFINE_NAME found in _defines.fos
	- $iflags FLAG1 FLAG2 FLAG3
		Expands into bitwise or combination of ITEM_* flags defined in _defines.fos.
		The 'ITEM_' prefix is automatically appended before each flag name.
		
	Reverse flags performs the following operations:
	
	- Type field is replaced with '$def' macro described above
	- Flags field is replaced with corresponding '$iflags' macro described above


	Example use:
	
		python3 protoprocessor.py folder1 --output folder2
	
	Parses and preprocesses all .fopro files in 'folder1', expanding all of
	the macros. The processed .fopro files are saved to 'folder2'.
	
		python3 protoprocessor.py folder1 --output folder2 --reverse
	
	Performs the reverse substitution on .fopro files in 'folder1'. Results
	are saved in 'folder2'.
	
		python3 protoprocessor.py my_folder --output my_folder
	
	Preprocesses and overwrites the original files in 'my_folder'. You should
	take backups before doing this.
	
		python3 protoprocessor.py my_folder
	
	Performs a dry preprocessing run. None of the results are saved.
"""

_iflags_re = re.compile(r'\$iflags\s+(.+)$', re.I)
_def_re = re.compile(r'\$def\s+([^\s]+)', re.I)

def process_macros(key, value, defines, iflags):
	"""
		Process macros in a proto key-value pair
	"""
	
	# $def
	m = _def_re.match(value)
	if m:
		if not m[1] in defines:
			raise RuntimeError("Unknown define {}".format(m[1]))
		return defines[m[1]]
	# $iflags
	m = _iflags_re.match(value)
	if m:
		lst = m[1].split()
		val = 0
		for df in lst:
			defname = "ITEM_" + df
			if not defname in defines:
				raise RuntimeError("Unknown item flag {}".format(defname))
			val = val | defines[defname]
		return str(val)
	return None

def process_reverse(key, value, defines, iflags):
	"""
		Convert proto key value pair into one with macros for more readability
	"""
	
	# Convert 'Flags' field into $iflags format
	if key == "Flags":
		flags = ""
		try:
			value = int(value)
		except:
			# Failed to parse value as integer, just return
			return None
		idx = 0
		# go through all the bits in the value
		while value > 0:
			exp = 2**idx
			assert value >= exp
			if value & exp:
				value -= exp
				if exp not in iflags["item_flags"]:
					raise RuntimeError("No item flag found for value bit {}".format(exp))
				flag_name = iflags["item_flags"][exp]
				flags = flags + " " + flag_name
			idx += 1
		if len(flags) > 0:
			return "$iflags" + flags
	
	# Convert 'Type' field into $def format
	if key == "Type":
		try:
			value = int(value)
		except:
			return None
		if value in iflags["item_types"]:
			return "$def " + iflags["item_types"][value]
	return None


if __name__ == "__main__":
	import sys
	import os
	import argparse
	parser = argparse.ArgumentParser(description="fopro preprocessor")
	parser.add_argument("input", type=str)
	parser.add_argument("--output", type=str)
	parser.add_argument("--reverse", action="store_true")
	parser.add_argument("--server-path", type=str)
	args = parser.parse_args()
	output_path = args.output
	reverse = args.reverse
	input_folder = args.input
	server_path = args.server_path or "."
	spath = server.locate_server(server_path)
	
	if spath is None:
		print("Failed to locate server path: cannot load server files", file=sys.stderr)
		sys.exit(1)
	
	defines = headerparser.parse_header_file(spath, "scripts/_defines.fos")
	defines = dict(defines)
	iflags = headerparser.get_item_flags(defines)
	
	process_func = process_reverse if reverse else process_macros
	
	if output_path:
		if not os.path.exists(output_path):
			os.makedirs(output_path)
	
	protos = protofile.load_freestanding_proto_files(input_folder)
	#protos = protofile.load_proto_files(spath)
	for x in protos:
		x.read_file()
		x.read_sections()
		update_count = 0
		proto_cnt = len(x.sections)
		print("Checking protofile at {} ({}), {} protos".format(x.name, "ACTIVE" if x.active else "INACTIVE", proto_cnt), file=sys.stderr)
		for pid, protosec in x.sections.items():
			changed = False
			for k, v in protosec.proto.data.items():
				try:
					procd = process_func(k, v, defines, iflags)
					if procd:
						protosec.proto.data[k] = procd
						changed = True
						update_count += 1
				except RuntimeError as e:
					print("At {} on proto {} starting at line {}: {}".format(x.name, pid, protosec.line_range[0], e))
			if changed:
				x.update_proto(pid, protosec.proto.data)
		if update_count > 0:
			print("Updated {} proto fields".format(update_count))
		if output_path:
			outfile = os.path.join(output_path, x.name)
			with open(outfile, "wt") as of:
				for l in x.lines:
					print(l, file=of)
