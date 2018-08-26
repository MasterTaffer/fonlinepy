import fonlinepy.protofile as protofile
import fonlinepy.headerparser as headerparser
import fonlinepy.server as server
import re

"""
	Give statistics of fopro files in folder.
	
	Usage
	
		python3 protolist.py input_folder
	
	Prints proto conflicts of fopro files in 'input_folder'
	
		python3 protolist.py input_folder --free 100
	
	Prints 100 first free PIDs not used in the fopro files in 'input_folder'
	
		python3 protolist.py input_folder --locate 5261
	
	Finds the location of PID 5261 in 'input_folder'
"""

if __name__ == "__main__":
	import sys
	import os
	import argparse
	parser = argparse.ArgumentParser(description="fopro statistics")
	parser.add_argument("input", type=str)
	parser.add_argument("--free", type=int)
	parser.add_argument("--locate", type=int)
	parser.add_argument("--active-only", action="store_true")
	parser.add_argument("--print", action="store_true")
	args = parser.parse_args()
	input_folder = args.input
	free_pids = args.free
	locate = args.locate
	active_only = args.active_only
	print_protos = args.print
	
	total_protos = 0
	
	proto_id_dict = {}
	proto_ids = []
	
	protos = protofile.load_freestanding_proto_files(input_folder)
	for x in protos:
		if active_only and not x.active:
			continue
		x.read_file()
		x.read_sections()
		update_count = 0
		proto_cnt = len(x.sections)
		if print_protos:
			print("Proto file {} ({}) containing {} protos".format(x.name, "ACTIVE" if x.active else "INACTIVE", proto_cnt))
		total_protos += proto_cnt
		for pid, sect in x.sections.items():
			fn = x.name
			line = sect.line_range[0]
			proto_ids.append(pid)
			if pid in proto_id_dict:
				print("Proto conflict, PID {}: first occurence in {} line {}, conflicting occurence in {} line {}".format(pid, proto_id_dict[pid][0], proto_id_dict[pid][1], fn, line), file=sys.stderr)
			else:
				proto_id_dict[pid] = (fn, line)
	if free_pids:
		proto_ids = sorted(proto_ids)
		p_idx = 0
		idx = 1
		while free_pids > 0:
			if len(proto_ids) <= p_idx:
				print(idx)
				free_pids -= 1
			else:
				if proto_ids[p_idx] > idx:
					print(idx)
					free_pids -= 1
				else:
					p_idx += 1
			idx += 1
	if locate:
		if not locate in proto_id_dict:
			print("PID {} not found".format(locate), file=sys.stderr)
		else:
			print("PID {} found in {} line {}".format(locate, proto_id_dict[locate][0], proto_id_dict[locate][1]))
