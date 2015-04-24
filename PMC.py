
import subprocess,os,urllib.request,urllib.parse,re,socket,time,threading

class PM_Catcher_Error(Exception):
	pass

class Notify(object):
	def __init__(self, message, user):
		self.Support   = {
					"gnome": "GNOME"
				}
		self.Structure = """%(user)s: %(message)s"""
		self.Session   = os.environ.get("DESKTOP_SESSION")
		if self.Session not in self.Support:
			raise PM_Catcher_Error(
					"Unsupported DESKTOP_SESSION `%s`; Private message Coil with this message to request support." % (
						self.Session
					)
				)
		else:
			if hasattr(self, self.Support[self.Session]):
				getattr(self, self.Support[self.Session])(message, user)

	def SHELLCMD(self, command):
		subprocess.Popen( command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE )

	def GNOME(self, message, user):
		Cmd = """notify-send "Private message received."  "{}" -u normal""".format(
				self.Structure % ({
					"user":    user.capitalize(),
					"message": message
				})
			)
		self.SHELLCMD(command=Cmd)

class PrivateMessages(object):
	def __init__(self, username, password):
		self.AUTH = re.search("auth.chatango.com=(.*?);",
				urllib.request.urlopen("http://chatango.com/login", urllib.parse.urlencode(
					{
						"user_id":     username.lower(),
						"password":    password,
						"storecookie": "on",
						"checkerrors": "yes"
					}
				).encode()).getheader("Set-Cookie")
			).group(1)
		self.THREADS = dict()
		self.THREADS.setdefault("Recv", None)
		self.THREADS.setdefault("Hrbt", None)
		if self.AUTH == "":
			raise PM_Catcher_Error("Invalid or unaccepted password.")
		else:
			self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.Socket.connect(("c1.chatango.com", 5222))
			self.Send("tlogin:%s:2:\x00"%(self.AUTH))
			while 1:
				time.sleep(1)
				self.THREADS["Recv"] = threading.Timer(0.1, self.Recv, args=())
				self.THREADS["Hrbt"] = threading.Timer(20, self.Hrbt, args=())
				for THREAD in self.THREADS.values():
					THREAD.daemon = True
					THREAD.start()

	def Recv(self):
		BUFFER  = self.Socket.recv(1024).decode("latin-1").rstrip("\r\n").split(":")
		BUFFERS = {"\r\n\x00": "IGNORE", "msg":"RecvMsg"}
		if BUFFER[0] in BUFFERS:
			Action = BUFFERS[BUFFER[0]]
			if Action != "IGNORE":
				if hasattr(self, "Act_" + Action):
					getattr(self, "Act_" + Action)(BUFFER[1:])

	def Act_RecvMsg(self, buffer):
		Username = buffer[0]
		Message  = ":".join(buffer[5:])
		Message  = re.sub("<n(.*?)>|<m v=\"(.*?)\">|<g (.*?)>|</g>|</m>|\r\n\x00", "", Message)
		Notify(Message, Username.lower())

	def Hrbt(self):
		self.Send("\r\n\x00")

	def Send(self, data):
		try:
			self.Socket.send(bytes(data,"utf-8"))
		except Exception as e:
			raise PM_Catcher_Error(e)

if __name__ == "__main__":
	PrivateMessages( "Usernamehere" , "Passwordhere" )
