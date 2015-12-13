from web_tasker import app
import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)