__version__ = "0.0.1"

try:
	from .vcentersession import VCenterSession
	from .rdp import rdp_file
	from jinja2 import Template
except:
	pass

import sys
import os
import logging
from . import tokens
import json
from pathlib import Path
from datetime import datetime

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stderr)
log.setLevel(os.environ.get("LOGLEVEL", "WARN"))

def test():
	return ('200 OK',
		[('Content-Type','text/html')],
		[b"Hello World"])

def notfound(message='Unknown'):
	responsehtml = "<html><head><title>Not Found</title></head><body><h1>Not Found</h1>%s</body></html>" % str(message)
	return ('404 Not Found', 
			[
				('Content-Type','text/html'),
				('Content-Length', str(len(responsehtml)))
			],
			[responsehtml.encode('ascii')])

def server_error(error="Unknown Error"):
	responsehtml = "<html><head><title>Bad Request</title></head><body><h1>Bad Request</h1>%s</body></html>" % str(error)
	return ('400 Bad Request', 
			[
				('Content-Type','text/html'),
				('Content-Length', str(len(responsehtml)))
			],
			[responsehtml.encode('ascii')])

def not_authorized(error="Not Authorized"):
	responsehtml = "<html><head><title>Not Authorized</title></head><body><h1>Not Authorized</h1></body></html>"
	return ('401 Not Authorized', 
			[
				('Content-Type','text/html'),
				('Content-Length', str(len(responsehtml)))
			],
			[responsehtml.encode('ascii')])

def rdp(ip_address=None):
	if isinstance(ip_address, list) and len(ip_address) > 0:
		ip_address = ip_address[0]
	elif isinstance(ip_address, str):
		pass
	else:
		raise TypeError("Invalid parameter value")
	
	rdp_data = rdp_file(ip_address)
	return ("200 OK",
			[
				('Content-Disposition', 'attachment; filename=samm-connection.rdp'),
				('Content-Length', str(len(rdp_data))),
				('Content-Type', 'application/x-rdp')
			],
			rdp_data.encode('ascii'))

def vmdetail(hostedmachinename=None):
	vc = VCenterSession(os.environ.get('SAMM_CONFIG', "/app/conf.json"))
	if hostedmachinename is None:
		raise KeyError("Virtual Machine not found")
	data = vc.search_vm(hostedmachinename)
	if len(data) < 1:
		raise KeyError("Virtual Machine not found")
	return ("302 Found",
		[
			("Location", "%s/ui/app/vm;nav=h/urn:vmomi:VirtualMachine:%s:%s/summary?navigator=tree" % (
				vc.config['vcenter_url'], data[0]['vm'], vc.config['vcenter_guid'])
			),
			("Content-Type", "text/html; charset=UTF-8"),
			("Content-Length", "0")
		]
		)

def hostdetail(hostingservername=None):
	vc = VCenterSession(os.environ.get('SAMM_CONFIG', "/app/conf.json"))
	if hostingservername is None:
		raise KeyError("Host not found")
	data = vc.search_host(hostingservername)
	if len(data) < 1:
		return KeyError("Host not found")
	return ("302 Found",
		[
			("Location", "%s/ui/app/host;nav=h/urn:vmomi:HostSystem:%s:%s/summary" % (
				vc.config['vcenter_url'], data[0]['host'], vc.config['vcenter_guid'])
			),
			("Content-Type", "text/html; charset=UTF-8"),
			("Content-Length", "0")
		]
		)

def updatecreds(**kwargs):
	log.info("Received body data=%s", kwargs)
	token = kwargs.get("token")
	if token is None:
		log.error("No token found in request")
		return not_authorized()

	if isinstance(token, list) and len(token) > 0:
		token = token[0]

	auth = tokens.verify_token(token)
	if not isinstance(auth, dict):
		log.error("Invalid token. token=%s" % token)
		return not_authorized()

	if auth.get("dashboard", "") != "SAMM Windows Credentials Update":
		log.error("Invalid dashboard. auth=%s" % auth)
		return not_authorized()


	auth_method = kwargs.get("auth_method")
	if auth_method == "userpass":
		username = kwargs.get("username")
		password = kwargs.get("password")
		with open("/private/samm.env", "w", encoding="utf-8") as file:
			file.write(f"CIM_USERNAME={username}\n")
			file.write(f"CIM_PASSWORD={password}\n")
			file.write("CIM_METHOD=kerberos\n")
		log.info("creating userpass")
	elif auth_method == "keytab":
		principal = kwargs.get("principal")
		ktf = kwargs.get("files", {}).get("keytab_file")
		ktf.save_as('/private/samm.keytab')
		with open("/private/samm.env", "w", encoding="utf-8") as file:
			file.write(f"CIM_USERNAME={principal}\n")
			file.write("KRB5_CLIENT_KTNAME=/etc/krb5.keytab\n")
			file.write("CIM_METHOD=kerberos\n")
		log.info("creating keytab")

	filepath = Path(__file__).parent / "docs/samm-update-credentials.html"
	with filelpath.open("rb") as f:
		body = f.read()

	return ("200 OK",
		[
			("Content-Type", "text/html; charset=utf-8"),
			("Content-Length", str(len(body))),
		], body)

def gettoken(**kwargs):
	user = kwargs.get("user", "")
	if isinstance(user, list):
		user = "".join(user)
	dashboard = kwargs.get("dashboard", "")
	if isinstance(dashboard, list):
		dashboard = "".join(dashboard)
	t = tokens.generate_token(user, dashboard)
	body = json.dumps({"token": t})
	return ("200 OK",
		[
			("Content-Type", "application/json; charset=utf-8"),
			("Content-Length", str(len(body)))
		], [body.encode('utf-8')])

def private(**kwargs):
	log.debug("Private request: kwargs='%s'", str(kwargs))
	filepath = Path(__file__).parent / "docs/samm-file-manager.html"
	with filepath.open("r") as f:
		temp = Template(f.read())

	items=[]
	privatepath=Path("/private")
	first = True
	for f in privatepath.iterdir():
		if f.is_file():
			modified = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
			line=f"{{ name: '{f.name}', type: 'file', size: {f.stat().st_size}, modified: '{modified}'}},"
			items.append(line)

	body = temp.render(name="Hello", items=items).encode("utf8")
	return ("200 OK",
		[
			("Content-Type", "text/html; charset=utf-8"),
			("Content-Length", str(len(body))),
		], body)
