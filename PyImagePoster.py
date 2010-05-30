#!/usr/bin/env python
#
import os, sys, re, random, string

# ======================================================================
# ======================================================================
"""
	Step through the package names.
		try to import each one.
		if it wont import
		 try to use easy_install to install it
			then try again.
"""
package_list = ["logging", "poster", "urllib2", "getpass"]
modules_missing = False
count = 0

while not modules_missing and count < len(package_list):
	package = package_list[count]

	print "trying to import %s " % package
	try :
		exec("import %s" % package)
		print "imported %s " % package
	except :
		print "[ %s ] is missing. " % package
		modules_missing.append(package)

	count = count + 1

if not modules_missing :
	print "Required Python Modules found, continuing..."
else:
	print "Required Python Modules Missing."
	print "You need to install some Python Modules before this script will do anything..."
	print "-= First =\n\tsudo apt-get install python-setuptools"
	print "-= Second =- \n install the missing modules"
	for package in modules_missing :
		print "\tsudo easy install %s " % package
	exit()

# ======================================================================
# ======================================================================

class ImageHostingUploader:
	""" Class doc """
	application_name = "PyImagePoster"
	hosts ={
		"imagebin.org" : {
			"default" : True,
			"formdata" : {
				"nickname" : "$username$",
				"title" : "$title$",
				"description" : "$title$",
				"disclaimer_agree" : "Y",
				"Submit" : "Submit",
				"mode" : "add"
			},
			"imagefield" : "image",
			"host_url" : "http://imagebin.org/",
			"upload_url" : "index.php?page=add",
			"needle" : r"""(?i)index.php\?mode=image&id=(?P<image_id>[0-9]+)""",
			"show_url" : lambda id: "http://imagebin.org/%s" % id,
			"file_rules" : lambda file: os.rename(file,file.replace("png","jpg")),
		},
		
		"localhost"	: {
			"default" : False,
			"formdata" : {
				"user" : "$username$",
			},
			"imagefield" : "image",
			"host_url" : "http://localhost:5000",
			"upload_url" : "/upload_image",
			"needle" : r""".*""",
			"show_url" : lambda str: str,
			"file_rules": lambda file: file,
		}
		
	}
	template_tags = {
		"username"		: lambda x,y: ''.join (random.choice (string.letters) for ii in range (len(y) + 1)),
		"filename"		:	lambda x,y: os.path.abspath(x),
		"title"				: lambda x,y: os.path.split(x)[1],
	}
	nautilus = False
	target_host = None
	logger = None
	default_host = "imagebin.org"
	
	def __init__ (self):
		""" Class initialiser """
		poster.streaminghttp.register_openers()
		self.application_conf_path = self.assure_path( '/home/%s/.%s' % (getpass.getuser(), self.application_name) )

		self.log_file = logging.FileHandler("%s/debug.log" % self.application_conf_path )
		self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		self.log_file.setFormatter(self.log_formatter)

		self.logger = logging.getLogger(self.application_name)
		self.logger.addHandler(self.log_file)
		self.logger.setLevel(logging.INFO)

	def start(self, host, files):
		hostnames = self.hosts.keys()
		cond = ["%s %s" % (host, name) for name in hostnames ]
		
		self.logger.info(".-= Starting upload =-.".center(72) )
		self.logger.info((".-= %s =-." % self.random_string(20) ).center(72) )
		self.logger.info("Uploading %s file" % len(files))
		self.logger.info("testing for host %s" % host)
		
		if host in hostnames :
			self.logger.info("host setup found for [ %s ]" % host) 
			self.target_host = self.hosts[host]
			output = []
			for file in files :
				status = """ "Uploading : %s" """ % file
				self.notify_bubble("gtk-go-up", status)
				output.append(self.upload(file))

			output =  (" , ".join(output))
			if uploader.nautilus :
				self.zenity_info(output)
			os.system("echo %s | xsel -i -b" % output )
			status = """ "Uploaded : %s \n paste links now with ctrl + v" """ % output
			self.notify_bubble("gtk-paste",status)
		else :
			self.logger.info("Invalid host, consider providing an INI file for your chosen host.")
			
	def fill_template (self,query,file):
		""" Function doc """
		output = None
		tags = self.template_tags
		query = re.sub("\$","",query)
		if query in tags.keys() :
			output = tags[query](file,query)
			self.logger.info("Replacing template tag [%s] with [%s]" % (query, output) )

		return output
		
	def assure_path (self, path):
		""" checks if it exists and makes it if it doesnt """
		if not os.path.exists(path):
			os.makedirs(path)
		return path

	def is_file(self,file):
		(path,filename) = os.path.split(file)
		if not os.path.exists(path) :
			return False
		else :
			if not os.path.isfile(file) :
				return False
		return True
		
	def random_string (self, length):
		return ''.join (random.choice (string.letters) for ii in range (length + 1))
		
	def notify_bubble(self, icon, msg):
		print msg
		os.popen("notify-send --icon=%s %s" % (icon,msg) )

	def upload(self,file):
		""" Function doc """
		target = self.target_host
		
		host = target["host_url"]
		upload_url = "%s%s" % (host, target["upload_url"] )
		data = target["formdata"]

		status = "Beginning upload of [ %s ] to [ %s ]" % (file,host) 
		self.logger.info(status)
		
		for key,value in data.iteritems():
			if "$" in value : 
				new_value = self.fill_template(value,file)
				if(new_value==None):
					self.logger.error("Could not find template tag : %s" % value)
				else:
					data[key] = new_value
		
		data[target["imagefield"]] = open(file,"rb")

		self.logger.info("Uploading with formdata [ %s ]" % data )
		datagen, headers = poster.encode.multipart_encode(data)

		self.logger.info("Building request object")
		request = urllib2.Request(upload_url, datagen, headers)

		self.logger.info("Sending formdata")
		response = urllib2.urlopen(request).read()

		self.logger.info("Searching response for imageID")
		match_obj = re.search( target["needle"], response )

		if match_obj != None :
			image_id = match_obj.group('image_id')
			if image_id != None :
				self.logger.info("imageID : %s" % image_id)
				url = target["show_url"](image_id)
				return url
			else :
				self.notify_bubble("gtk-error", "There was an error uploading the image.")
				self.logger.warn("Page returned data, but could not find image_id.")
				self.logger.debug(match_obj.groups())
		else :
			self.notify_bubble("gtk-error", "There was an error uploading the image.")
			self.logger.info("Did not return match id")
		
if __name__ == "__main__" :
	uploader = ImageHostingUploader()

	uploader.logger.info("starting %s" % len(sys.argv) )
	host = uploader.default_host
	#uploader.zenity_selection("choose a server", ["Pick", "Server"], [("TRUE %s" if data["default"]==True else "FALSE %s") % host for host,data in uploader.hosts.iteritems() ] )

	nautilus_selection = os.getenv("NAUTILUS_SCRIPT_SELECTED_FILE_PATHS")
	if nautilus_selection != None :
		uploader.nautilus = nautilus_selection
		uploader.logger.info("Using nautilus selection : %s " % nautilus_selection)
		files = re.split("\n",nautilus_selection)
	else:
		uploader.nautilus = False
		files = [x for x in sys.argv[1:]]
		uploader.logger.info("Using bash parameters : %s " % files)

	uploader.logger.info("Using host : %s" % host)
	
	uploader.start(host, files)
