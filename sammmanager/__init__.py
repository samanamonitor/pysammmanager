__version__ = "0.0.1"

try:
	from .vcentersession import VCenterSession
	from .rdp import rdp_file
except:
	pass

import os

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
	responsehtml = "<html><head><title>Internal Server Error</title></head><body><h1>Internal Server Error</h1>%s</body></html>" % str(error)
	return ('500 Internal Server Error', 
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

