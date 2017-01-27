import sys

sys.path.insert(0, "/var/www/html/wocat")

import bottle
import service
application = bottle.default_app()
