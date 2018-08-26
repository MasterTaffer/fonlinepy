import os
import re
import logging
import fonlinepy.protoparser as protoparser
from collections import OrderedDict

"""

	Read FOnline item fopro files
	
"""

PROTO_PATH = "proto/items"

class ProtoFileSection:
	def __init__(self, line_range, lines):
		self.line_range = line_range
		self.proto = protoparser.ParsedProto(lines[1:])

class ProtoFile:
	def __init__(self, name, path, active=None, last_modification=None):
		self.name = name # The name of the ProtoFile, filename
		self.path = path # File path
		self.active = active # whether the fopro is listed in items.lst
		self.last_modification = last_modification # last modification timestamp
		self.lines = [] # list of all lines in the fopro file
		self.sections = OrderedDict() # dictionary of proto sections in the file, with PID as key

	def read_file(self):
		with open(self.path) as f:
			self.lines = [l.rstrip("\n") for l in f]

	def read_sections(self):
		active_section = False
		
		last_proto_start = 0
		def next_proto(line_index):
			nonlocal active_section
			nonlocal last_proto_start 
			if active_section:
				try:
					pfs = ProtoFileSection((last_proto_start, line_index), self.lines[last_proto_start:line_index])
					self.sections[pfs.proto.id] = pfs
				except RuntimeError as a:
					logging.warning("Illegal proto file %s: invalid proto definition at lines %s - %s",
						self.path, last_proto_start+1, line_index+1, exc_info=a)
			active_section = True
			last_proto_start = line_index

		for i, l in enumerate(self.lines):
			dl = l.strip()
			
			if len(dl) == 0:
				continue
			
			if dl == "[Proto]":
				next_proto(i)

			if not active_section:
				
				if dl[0] == "#":
					continue
				logging.warning("Illegal proto file %s: Garbage in header", self.path)
				continue
		next_proto(len(self.lines))
		logging.info("Loaded %s protos from %s", len(self.sections), self.path)

	def shift_ranges(self, amount, starting_from = 0):
		for e in self.sections.values():
			if e.line_range[0] > starting_from:
				e.line_range = [e.line_range[0] + amount, e.line_range[1] + amount]
				continue

	def replace_range(self, proto_fields, r_range):
		outd = ["[Proto]"] + list(proto_fields) + [""]
		new_range = (r_range[0], r_range[0] + len(outd))
		len_diff = new_range[1] - r_range[1]
		self.lines[r_range[0]:r_range[1]] = outd
		self.shift_ranges(len_diff, r_range[0])
		return new_range

	def update_proto(self, proto_id, proto_dict):
		gp = protoparser.GeneratedProto(proto_id, proto_dict)
		if proto_id in self.sections:
			section = self.sections[proto_id]
			section.proto = gp
			new_range = self.replace_range(gp.as_lines(), section.line_range)
			section.line_range = new_range
		else:
			new_range = self.replace_range(gp.as_lines(), (len(self.lines), len(self.lines)))
			pfs = ProtoFileSection(new_range, self.lines[new_range[0]:new_range[1]])
			self.sections[proto_id] = pfs

"""
	Load files from directory target_path
"""
def load_freestanding_proto_files(target_path):
	items_lst_path = os.path.join(target_path, "items.lst")

	proto_files = []
	active_protos = []

	try:
		with open(items_lst_path) as f:
			lines = f.readlines()
			lines = map(str.strip, lines)
			lines = filter(len, lines)
			active_protos.extend(lines)
	except OSError as e:
		logging.warning("Failed to open '%s': %s", items_lst_path, e)
	
	if len(active_protos) == 0:
		logging.warning("No active protofiles")
	else:
		logging.info("%s active protofiles", len(active_protos))

	found_active_protos = 0
	fopro_regex = re.compile(r'.+\.fopro$')
	try:
		with os.scandir(target_path) as scandir:
			for x in scandir:
				if not fopro_regex.match(x.name):
					continue

				active = x.name in active_protos
				st = x.stat()
				proto_files.append(ProtoFile(x.name, x.path, active, st.st_mtime))
				if active:
					found_active_protos += 1
	except OSError as e:
		logging.warning("Failed to read directory '%s'", target_path)
	
	logging.info("Read %s out of %s active proto files",found_active_protos, len(active_protos))
	if found_active_protos != len(active_protos):
		logging.warning("Failed to read all active proto files")
	logging.info("Read %s inactive proto files",len(proto_files) - found_active_protos)

	return proto_files

"""
	Load files from server server_path
"""
def load_proto_files(server_path):
	target_path = os.path.join(server_path, PROTO_PATH)
	return load_freestanding_proto_files(target_path)

if __name__ == "__main__":
	
	"""
	# Creating & printing a proto file
	pf = ProtoFile("test.fopro", "test.fopro")
	
	# Uncomment these lines to read the file 'test.fopro' instead of starting
	# from an empty fopro file:
	#pf.read_file() # read lines from the file
	#pf.read_sections() # read Proto sections from the file

	# Create new proto
	protodict = {"Type": 24, "Cost": 5, "A": 1, "D": 1, "C": 1, "R": 1, "fSDSDF": 1}
	
	# Add the proto
	pf.update_proto(9013, protodict)

	# Now print the new proto file
	for l in pf.lines:
		print(l)
	"""
	
	
	import fonlinepy.server as server
	spath = server.locate_server(".")
	if spath is None:
		logging.error("Failed to locate server path")
	else:
		protos = load_proto_files(spath)
		for x in protos:
			x.read_file()
			x.read_sections()
			proto_cnt = len(x.sections)
			print("{},{},{}".format(x.name, "ACTIVE" if x.active else "INACTIVE", proto_cnt))


