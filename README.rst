What is Climate REST API
========================
The REST API module provides a programmatic interface to climate database based on geotiff files.

Description
-----------
The service return the specific index value from world geo coordinate:

http://maprooms.ciat.cgiar.org/climatewizard/service

Parameters
----------
**lat** (float)  (Required) 
    Latitude from the geocoordinate

**lon** (float)  (Required) 
    Longitude from the geocoordinate

**index** (str)  (Required) 
    Climate index
    **Permitted values:** txavg, tnavg, txx, tnn, gd10, hd18, cd18, tx90, tx90p, tx10p, tn90p, tn10p, fd, gsl, hwdi, ptot, CDD, r02, r5d, sdii, r90p

**scenario** (str) (Required) 
	Scenario applied
	**Permitted values:** historical, rcp45, rcp85

**gcm** (str) (optional) 
	Model applied
	**Permitted values:** ACCESS1-0, ensemble_lowest
	**Default:** ensemble_lowest




**range** (str) (optional)
	Rage of years will be returned, the range must be separated by dash (-). 
	Ex: “2010-2020”
	Default: For scenario = “historical” is "1976-2005". For scenario “rcp45 and rcp85” is "2040-2069"

**avg** (boolean) (optional)
	Define if the result is the average of the range selected or if it is a list of values
    **Default:** true

Return Values
--------------
Returns the values in json format. If the data is not found a message error will be returned.

Examples
--------
Example #1
----------
http://maprooms.ciat.cgiar.org/climatewizard/service?lat=9.58&lon=-74.41&index=CD18&scenario=rcp45&gcm=ACCESS1-0

```
Output:

{
acronym: "CD18",
model: "ACCESS1-0",
-values: (1)[
-{
date: "avg_2040-2069",
value: "464847.6"
}
],
name: "cooling degree days",
scenario: "rcp45"
}
```
Example #2
----------
http://maprooms.ciat.cgiar.org/climatewizard/service?lat=9.58&lon=-74.41&index=CD18&scenario=rcp45&gcm=ACCESS1-0&range=false

```
Output:

{
acronym: "CD18",
model: "ACCESS1-0",
-values: (94)[
-{
date: 2006,
value: 411926
},
-{
date: 2007,
value: 433230
},

ETC …

-{
date: 2098,
value: 516298
},
-{
date: 2099,
value: 500290
}
],
name: "cooling degree days",
scenario: "rcp45"
}
```

Example #3
----------
http://maprooms.ciat.cgiar.org/climatewizard/service?lat=9.58&lon=-74.41&index=CD18&scenario=historical&gcm=ACCESS1-0&range=1960-1970&avg=false

```
Output

{
acronym: "CD18",
model: "ACCESS1-0",
-values: (6)[
-{
date: 1960,
value: 3937.16
},
-{
date: 1961,
value: 3869.43
},
-{
date: 1962,
value: 3792.88
},
-{
date: 1963,
value: 3761.62
},
-{
date: 1964,
value: 3633.05
},
-{
date: 1965,
value: 3933.23
}
],
name: "cooling degree days",
scenario: "historical"
}
```

Installing the REST API
-----------------------
The REST API deploys as a standard webapp for your servlet container / apache.
The technology used is python, specifically the libraries GDAL and Bottle.

APACHE MOD_WSGI
Instead of running your own HTTP server from within Bottle, you can attach Bottle applications to an Apache server using mod_wsgi.
All you need is an app.wsgi file that provides an application object. This object is used by mod_wsgi to start your application and should be a WSGI-compatible Python callable.
File /var/www/html/yourapp/app.wsgi:

.. code-block:: python

	import os
	# Change working directory so relative paths (and template lookup) work again
	sys.path.insert(0, "/var/www/html/yourapp")

	import bottle
	import service
	# ... build or import your bottle application here ...
	# Do NOT use bottle.run() with mod_wsgi
	application = bottle.default_app()

The Apache configuration may look like this:

```
WSGIDaemonProcess yourapp user=ubuntu group=ubuntu processes=1 threads=5
application-group=%{GLOBAL}
WSGIScriptAlias /climate /var/www/html/yourapp/app.wsgi
<Directory /var/www/html/yourapp/app.wsgi>
  WSGIProcessGroup %{GLOBAL}
  WSGIApplicationGroup %{GLOBAL}
  Order deny,allow
  Allow from all
</Directory>
```
