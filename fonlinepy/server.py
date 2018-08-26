import os
def locate_server(from_dir, climb=True):
	"""
		Locates FOnline server based on a few files and directories that
		should be there.
	"""
	def climber(dirpath):

		dirpath = os.path.realpath(dirpath)
		spl = os.path.split(dirpath)
		if len(spl[1]) == 0:
			dirpath = spl[0]
		yield(dirpath)
		while os.path.dirname(dirpath) != dirpath:
			dirpath = os.path.dirname(dirpath)
			yield(dirpath)


	def check_is_server_dir(dirpath):
		target_files = ["FOnlineServer.cfg"]
		target_dirs = ["proto", "scripts", "data"]
		
		target_files = map(lambda x: os.path.isfile(os.path.join(dirpath, x)), target_files)
		target_dirs = map(lambda x: os.path.isdir(os.path.join(dirpath, x)), target_dirs)
		if not all(target_files) or not all(target_dirs):
			return False
		return True
	if not climb:
		path = next(climber(from_dir))
		return path if check_is_server_dir(path) else None
	for dirpath in climber(from_dir):
		if check_is_server_dir(dirpath):
			return dirpath
	return None

if __name__ == "__main__":
	print(locate_server("."))
