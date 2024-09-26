from urllib.parse import parse_qs
import sammmanager

def application(env, start_response):
	path_info = env.get('PATH_INFO')
	query_string = parse_qs(env.get('QUERY_STRING'))
	try:
		_, _, func_name = path_info.rpartition('/')
		func = getattr(sammmanager, func_name)
		status, headers, body = func(**query_string)
	except AttributeError as e:
		status, headers, body = sammmanager.notfound(e)
	except KeyError as e:
		status, headers, body = sammmanager.notfound(e)
	except Exception as e:
		status, headers, body = sammmanager.server_error(error=str(e))
	start_response(status, headers)
	return body

if __name__ == "__main__":
	print("This script should only be executed by uwsgi.")
