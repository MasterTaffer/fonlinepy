import logging
from collections import OrderedDict

class Proto:
	def __init__():
		self.id = None
		self.data = OrderedDict()
		self.overrides = set()


	def _parse(self, lines):
		ls = map(lambda x: x.split("#")[0], lines)
		ls = map(str.strip, ls)
		ls = filter(len, ls)

		for x in ls:
			
			spl = tuple(map(str.strip, x.split("=")))
			if len(spl) != 2:
				raise RuntimeError("Invalid proto syntax")
			
			if len(spl[0]) == 0:
				raise RuntimeError("Invalid proto syntax")

			if spl[0] in self.data:
				self.overrides.add(spl[0])

			self.data[spl[0]] = spl[1]
		try:
			self.id = int(self.data["ProtoId"])
		except:
			raise RuntimeError("Proto definition does not contain a valid ProtoId")
		del self.data["ProtoId"]

	def as_lines(self):
		yield "{}={}".format("ProtoId", self.id)

		for x in self.data:
			yield "{}={}".format(x, self.data[x])

	def compare_fields(self, other):
		for x in self.data:
			if not x in other.data:
				return False
			if self.data[x] != other.data[x]:
				return False
		return True

class ParsedProto(Proto):
	def __init__(self, lines):
		"""
			Parses a single item proto from lines. The input lines should not
			contain the initial '[Proto]' line.
		"""
		self.lines = lines
		self.data = OrderedDict()
		self.overrides = set()
		self._parse(lines)

class GeneratedProto(Proto):
	def __init__(self, proto_id, proto_dict):
		self.data = proto_dict
		self.id = proto_id
