import json
from urllib3 import Timeout, PoolManager, make_headers

class VCException(Exception):
	pass

class VCUnauthenticated(VCException):
	pass

class VCenterSession:
	def __init__(self, config_file):
		with open(config_file, "r") as f:
			self.config = json.load(f)
		timeout = Timeout(
			connect=config.get("connection_timeout_seconds", 2.0), 
			read=config.get("read_timeout_seconds", 30.0))
		self.http = PoolManager(cert_reqs='CERT_NONE', timeout=timeout)
		self.session_id = ""
	def login(self):
		headers = make_headers(basic_auth="%s:%s" % (
			self.config['vcenter_username'],
			self.config['vcenter_password']))
		headers['Content-type'] = 'application/json'
		r = self.http.request('POST', "%s/api/session" % self.config['vcenter_url'], headers=headers)
		if r.status != 201:
			raise VCUnauthenticated
		self.session_id = json.loads(r.data.decode('ascii'))
	def _get(self, path):
		headers = {
			'Content-type': 'application/json',
			'vmware-api-session-id': self.session_id
		}
		r = self.http.request('GET', "%s%s" % (self.config['vcenter_url'], path), headers=headers)
		if r.status == 401:
			raise VCUnauthenticated(r.data)
		return json.loads(r.data.decode('ascii'))
	def logout(self):
		headers = {
			'Content-type': 'application/json',
			'vmware-api-session-id': self.session_id
		}
		self.http.request('DELETE', "%s/api/session" % self.config['vcenter_url'], headers=headers)
	def search_vm(self, name):
		uri = "/api/vcenter/vm?names=%s" % name
		try:
			data = self._get(uri)
		except VCUnauthenticated:
			self.login()
			data = self._get(uri)
		return data
	def search_host(self, name):
		uri = "/api/vcenter/host?names=%s" % name
		try:
			data = self._get(uri)
		except VCUnauthenticated:
			self.login()
			data = self._get(uri)
		return data
