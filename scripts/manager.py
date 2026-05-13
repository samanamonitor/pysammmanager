from urllib.parse import parse_qs
import sammmanager
import logging
import os
from pathlib import Path
from multipart import parse_form_data
from http import cookies
from datetime import datetime, timedelta, timezone

log = logging.getLogger(__name__)

log.setLevel(os.environ.get("LOGLEVEL", "WARN"))

class NotAuthorized(Exception):
	pass

def application(env, start_response):
	auth_cookie = env.get("HTTP_COOKIE", "")
	cookie = cookies.SimpleCookie()
	cookie.load(auth_cookie)
	sammcookie=cookie.get("samm_auth", cookies.Morsel()).value

	basepath = Path(os.environ.get('BASE_PATH', "/manager"))
	path_info = Path(env.get('PATH_INFO'))
	query_string = {}
	if env.get('REQUEST_METHOD', "") == "POST":
		query_string, files = parse_form_data(env)
		query_string["files"] = files
	else:
		query_string = parse_qs(env.get('QUERY_STRING'))

	log.info("Requests received. data=%s", env)
	try:

		if sammcookie is None:
			token = query_string.pop("token", "")
			if token == "":
				raise NotAuthorized
			cookie['samm_auth'] = token
		expire_date = datetime.now(timezone.utc) + timedelta(minutes=5)
		cookie_expires = expire_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
		cookie['samm_auth']['expires'] = cookie_expires
		cookie['samm_auth']['path'] = str(basepath)
		strcookie = cookie.output()
		start_response("302 Found", [
			(cookie.output()),
			("Location", path_info)
		])
		return b""

		func_name = path_info.relative_to(basepath).parent
		if str(func_name) == ".":
			func_name = path_info.relative_to(basepath).name
		else:
			query_string["localfile"] = str(path_info.relative_to(basepath).name)

		func = getattr(sammmanager, str(func_name))
		status, headers, body = func(**query_string)
	except NotAuthorized:
		log.error("Unauthorized")
		status, headers, body = sammmanager.not_authorized()
	except (AttributeError, ValueError) as e:
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
