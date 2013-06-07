# WSGI entry point to AppGateway

# Setup PYTHONPATH for imports to work
import sys
sys.path.insert(0, "/var/www/wsgi/AppGateway")

# Setup flask app as application to run by WSGI
from CISAppGateway import app as application

# Load the AppGateway configuration
from CISAppGateway import Config
Config.conf.load("/var/www/wsgi/AppGateway/AppGatewayProduction.json")

