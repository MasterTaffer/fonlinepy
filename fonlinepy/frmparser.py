import struct

"""

	Fallout FRM file parser
	
	Doesn't support palettes!
	
"""


def parse_frm_header(data):
	if len(data) < 0x004A:
		raise RuntimeError("Invalid FRM header")
	
	iheader = struct.unpack(">IHHH" , data[0:0x0A])
	ver = iheader[0]
	fps = iheader[1]
	act = iheader[2]
	num_frames = iheader[3]
	
	if ver != 0x04:
		raise RuntimeError("Unknown FRM version {}".format(ver))
	
	offsets = struct.unpack(">hhhhhhhhhhhh", data[0x0A:0x22])
	offsets = zip(offsets[0:6], offsets[6:12])
	
	direction_offsets = struct.unpack(">IIIIII", data[0x22:0x3A])
	
	return {
		"fps": fps,
		"num_frames": num_frames,
		"shifts": offsets,
		"direction_byte_offsets": direction_offsets
	}

def parse_frame_data(data, offset):
	w, h, size, shift_x, shift_y = struct.unpack(">HHIhh", data[offset:offset+0x0C])
	if w * h != size:
		raise RuntimeError("Invalid FRM frame size")


	pixels = data[offset+0x0C : offset+0x0C+size]

	return {
		"width" : w,
		"height" : h,
		"total_size_in_bytes" : 0x0C+size,
		"shift_x" : shift_x,
		"shift_y" : shift_y,
		"pixels" : pixels
	}

def parse_frm(data):
	FRAME_AREA_START = 0x03E
	header = parse_frm_header(data)
	proc_offs = {}
	direction_images = []
	for d in range(0, 6):
		proc_off = header["direction_byte_offsets"][d]
		orig_off = proc_off

		if proc_off in proc_offs:
			direction_images.append(proc_offs[proc_off])
			continue

		proc_off += FRAME_AREA_START
		images = []
		for i in range(0, header["num_frames"]):
			im = parse_frame_data(data, proc_off)
			proc_off += im["total_size_in_bytes"]
			images.append(im)

		proc_offs[orig_off] = images
		direction_images.append(images)
	return header, direction_images
testim = None

if __name__ == "__main__":
	"""
		Test program, loads and displays a FRM file (without correct palette).
		Requires numpy and matplotlib
	"""
	import numpy as np
	import matplotlib.pyplot as plt
	import argparse
	parser = argparse.ArgumentParser(description="FRM test program")
	parser.add_argument("input", type=str)
	args = parser.parse_args()
	ifile = args.input
	

	with open(ifile, "rb") as f:
		b = f.read()
		data = parse_frm(b)
		tim = data[1][0][0]
		arr = np.frombuffer(tim["pixels"], dtype=np.uint8)
		arr = np.reshape(arr, [tim["height"], tim["width"]])
		testim = arr
		plt.imshow(arr)
		plt.show()
		


