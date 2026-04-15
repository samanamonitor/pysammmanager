from urllib.parse import parse_qs
import sammmanager
import logging
import os
from multipart import parse_form_data

log = logging.getLogger(__name__)

log.setLevel(os.environ.get("LOGLEVEL", "WARN"))

class NotAuthorized(Exception):
	pass

def check_session(env):
	return True

def application(env, start_response):
	path_info = env.get('PATH_INFO')
	query_string = {}
	if env.get('REQUEST_METHOD', "") == "POST":
		query_string, files = parse_form_data(env)
		query_string["files"] = files
	else:
		query_string = parse_qs(env.get('QUERY_STRING'))

	log.info("Requests received. data=%s", env)
	try:
		if not check_session(env):
			raise NotAuthorized
		_, _, func_name = path_info.rpartition('/')
		func = getattr(sammmanager, func_name)
		status, headers, body = func(**query_string)
	except NotAuthorized:
		log.error("Unauthorized")
		status, headers, body = sammmanager.not_authorized()
	except AttributeError as e:
		log.exception(e.__class__.__name__)
		status, headers, body = sammmanager.notfound(e)
	except KeyError as e:
		log.exception(e.__class__.__name__)
		status, headers, body = sammmanager.notfound(e)
	except FileNotFoundError as e:
		log.exception(e.__class__.__name__)
		status, headers, body = sammmanager.notfound(e)
	except Exception as e:
		log.exception(e.__class__.__name__)
		status, headers, body = sammmanager.server_error(error=str(e))

	start_response(status, headers)
	return body

if __name__ == "__main__":
	print("This script should only be executed by uwsgi.")
