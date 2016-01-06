from web_tasker import app
import logging
#logging.basicConfig()

log = logging.getLogger()
log.setLevel(logging.ERROR)

sql_log = logging.getLogger('sqlalchemy.engine')
sql_log.setLevel(logging.DEBUG)

requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
