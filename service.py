from osgeo import gdal,ogr
from osgeo.gdalconst import *
import struct
import time
import sys,os, fnmatch
from bottle import route, request, response, template, run, get, post
import simplejson
import json
import sys
import numpy as np
import rasterio
from rasterstats import zonal_stats, raster_stats
from rasterstats.utils import VALID_STATS
from rasterstats.io import read_featurecollection, read_features
import fiona

def find(pattern, path):
    result = ""
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result = os.path.join(root, name)
    return result

def calcAvg (file, folder,wrange, lat, lon):
	name = file.split(folder)
	acroIndex = name[1].split("_")
	period = acroIndex[4].split("-")
	startDate = int(acroIndex[4].split("-")[0])
	lat = float(request.query.lat)
	lon = float(request.query.lon)
	ds = gdal.Open(folder+name[1], GA_ReadOnly)
	transf = ds.GetGeoTransform()

	px = (lon-transf[0])/transf[1]
	py = (lat-transf[3])/transf[5]

	if ds is None:
		print 'Failed open file'
		sys.exit(1)

	bands = ds.RasterCount
	avg = 0
	for band in range( bands ):
		band += 1
		if int(wrange[0]) <= int(band+startDate-1) <= int(wrange[1]):
			srcband = ds.GetRasterBand(band)
			structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
			bandtype = gdal.GetDataTypeName(srcband.DataType)
			intval = struct.unpack(fmttypes[bandtype] , structval)
			avg += round((float(intval[0])/100),2)

	if avg != 0:
		avg = avg / (int(wrange[1]) - int(wrange[0]) + 1)
	return avg

index = {'txavg':'Monthly mean maximum temperatures historical', 'tnavg':'Monthly mean minimum temperatures', 'txx':'Monthly maximum temperatures', 'tnn':'Monthly minimum temperatures', 'gd10':'growing degree days', 'hd18':'heating degree days', 'cd18':'cooling degree days', 'tx90':'90th percentile Tmax - one value per year', 'tx90p':'Generalized version: Pct of time T doesnt exceeds ref pd Nth percentile', 'tx10p':'Generalized version: Pct of time T doesnt exceeds ref pd Nth percentile', 'tn90p':'Generalized version: Pct of time T doesnt exceeds ref pd Nth percentile', 'tn10p':'Generalized version: Pct of time T doesnt exceeds ref pd Nth percentile', 'fd':'Frost days', 'gsl':'Thermal growing season length', 'hwdi':'Heat wave duration index wrt mean of reference_period', 'ptot':'Monthly total precip', 'cdd':'Consecutive dry days', 'r02':'Number of wet days > 0.2 mm/d', 'r5d':'Max consec 5 day precip', 'sdii':'simple daily precip intensity index', 'r90p':'calculate of precip due to this too'}
fmttypes = {'Byte':'B', 'UInt16':'H', 'Int16':'h', 'UInt32':'I', 
            'Int32':'i', 'Float32':'f', 'Float64':'d'}	
	

@get('/service')
def service():
	if not request.query.range:
		if request.query.scenario.lower() == "historical":
			wrange = ["1976","2005"]
		else:
			wrange = ["2040","2069"]
	elif request.query.range == "false":
		wrange = "false"
	else:
		wrange = request.query.range.split("-")

	if not request.query.gcm:
		wgcm = "ensemble_lowest"
	else:
		wgcm = request.query.gcm.lower()

	if not request.query.avg or request.query.avg == "true":
		wavg = True
	else:
		wavg = False

	# for convert to celsius
	if request.query.index.lower()=="txavg" or request.query.index.lower()=="tnavg" or request.query.index.lower()=="txx" or request.query.index.lower()=="tnn":
		factor=-273.15 
	else:
		factor=0
		
	fileName = request.query.index.lower()+"_bcsd_"+request.query.scenario.lower()+"_"+wgcm
	folderModels = "/mnt/data_climatewizard/AR5_Global_Daily_25k/out_stats_tiff/"
	folder = folderModels+wgcm+"/"
	allfiles = find(fileName+"*", folder)

	if allfiles:
		name = allfiles.split(folder)
		acroIndex = name[1].split("_")
		period = acroIndex[4].split("-")
		startDate = int(acroIndex[4].split("-")[0])
		json_output = {'name' : index[request.query.index.lower()], 'acronym':request.query.index,'model':wgcm,'scenario':request.query.scenario.lower() ,'values':[]}
		ds = gdal.Open(folder+name[1], GA_ReadOnly)
		if ds is None:
				print 'Failed open file'
				sys.exit(1)
		bands = ds.RasterCount

		if request.query.geojson:
			file = '/tmp/cwizard'+time.strftime("%H:%M:%S")+'.geojson'
			with open(file, 'w') as file_:
				file_.write(request.query.geojson)

			if request.query.stats:
				tstats = request.query.stats.split(",")
				rstats = []
				for stat in tstats:
					rstats.append(stat)
			else :
				rstats = ['min', 'max', 'median', 'mean', 'std','percentile_5','percentile_25','percentile_75','percentile_95']

			for band in range( bands ):
				band += 1
				if int(wrange[0]) <= int(band+startDate-1) <= int(wrange[1]):
					with fiona.open(file) as src:
						zs = zonal_stats(src, folder+name[1], band=band,stats=rstats)

					output_item = {'date' : int(band+startDate-1) , 'value' : zs[0]}
					json_output['values'].append(output_item)
			return json_output
		else:
			baselineAvg = 0
			if request.query.baseline:
				wbaseline = request.query.baseline.split("-")
				if (int(wbaseline[1]) - int(wbaseline[0])) < 19 :
					return {"error":"Baseline range must be equal or greater than 20 years"}
				elif request.query.scenario.lower() == "historical":
					return {"error":"Scenario must be different to historical"}
				else:
					baseFileName = request.query.index.lower()+"_bcsd_historical_"+wgcm
					baseFile = find(baseFileName+"*", folder)
					baselineAvg = calcAvg (baseFile, folder, wbaseline, float(request.query.lat), float(request.query.lon))
			lat = float(request.query.lat)
			lon = float(request.query.lon)
			
			transf = ds.GetGeoTransform()

			px = (lon-transf[0])/transf[1]
			py = (lat-transf[3])/transf[5]

			if wrange and wrange != "false":
				avg = 0
				for band in range( bands ):
					band += 1
					if int(wrange[0]) <= int(band+startDate-1) <= int(wrange[1]):
						srcband = ds.GetRasterBand(band)
						structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
						bandtype = gdal.GetDataTypeName(srcband.DataType)
						intval = struct.unpack(fmttypes[bandtype] , structval)
						if wavg:
							avg += (round((float(intval[0])/100),2))+factor
						else:
							output_item = {'date' : int(band+startDate-1) , 'value' : ((round((float(intval[0])/100),2))+factor)-baselineAvg}
							json_output['values'].append(output_item)
				if avg != 0 and wavg:
					avg = (avg / (int(wrange[1]) - int(wrange[0]) + 1)) - baselineAvg +factor
					output_item = {'date' : 'avg_'+wrange[0]+"-"+wrange[1] , 'value' : str(avg)}
					json_output['values'].append(output_item)
				elif avg == 0 and wavg:
					output_item = {'date' : 'avg_'+wrange[0]+"-"+wrange[1] , 'value' : 'out of range'}
					json_output['values'].append(output_item)
				return json_output

			else:
				for band in range( bands ):
					band += 1
					srcband = ds.GetRasterBand(band)
					structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
					bandtype = gdal.GetDataTypeName(srcband.DataType)
					intval = struct.unpack(fmttypes[bandtype] , structval)
					output_item = {'date' : int(band+startDate-1) , 'value' : ((round((float(intval[0])/100),2))+factor)-baselineAvg}
					json_output['values'].append(output_item)
				return json_output
	else :
		return {"error":"Data not found"}

@post('/service')
def do_service():
	if not request.query.range:
		if request.query.scenario.lower() == "historical":
			wrange = ["1976","2005"]
		else:
			wrange = ["2040","2069"]
	elif request.query.range == "false":
		wrange = "false"
	else:
		wrange = request.query.range.split("-")

	if not request.query.gcm:
		wgcm = "ensemble_lowest"
	else:
		wgcm = request.query.gcm.lower()

	if not request.query.avg or request.query.avg == "true":
		wavg = True
	else:
		wavg = False

	# for convert to celsius
	if request.query.index.lower()=="TXAVG" or request.query.index.lower()=="TNAVG" or request.query.index.lower()=="TXX" or request.query.index.lower()=="TNN":
		factor=-273.15 
	else:
		factor=0
		
	fileName = request.query.index+"_BCSD_"+request.query.scenario.lower()+"_"+wgcm
	folderModels = "/mnt/data_climatewizard/AR5_Global_Daily_25k/out_stats_tiff/"
	folder = folderModels+wgcm+"/"
	allfiles = find(fileName+"*", folder)

	if allfiles:
		name = allfiles.split(folder)
		acroIndex = name[1].split("_")
		period = acroIndex[4].split("-")
		startDate = int(acroIndex[4].split("-")[0])
		json_output = {'name' : index[request.query.index.lower()], 'acronym':request.query.index,'model':wgcm,'scenario':request.query.scenario.lower() ,'values':[]}
		ds = gdal.Open(folder+name[1], GA_ReadOnly)
		if ds is None:
				print 'Failed open file'
				sys.exit(1)
		bands = ds.RasterCount

		if request.query.geojson:
			file = '/tmp/cwizard'+time.strftime("%H:%M:%S")+'.geojson'
			with open(file, 'w') as file_:
				file_.write(request.query.geojson)

			if request.query.stats:
				tstats = request.query.stats.split(",")
				rstats = []
				for stat in tstats:
					rstats.append(stat)
			else :
				rstats = ['min', 'max', 'median', 'mean', 'std','percentile_5','percentile_25','percentile_75','percentile_95']

			for band in range( bands ):
				band += 1
				if int(wrange[0]) <= int(band+startDate-1) <= int(wrange[1]):
					with fiona.open(file) as src:
						zs = zonal_stats(src, folder+name[1], band=band,stats=rstats)

					output_item = {'date' : int(band+startDate-1) , 'value' : zs[0]}
					json_output['values'].append(output_item)
			return json_output
		else:
			baselineAvg = 0
			if request.query.baseline:
				wbaseline = request.query.baseline.split("-")
				if (int(wbaseline[1]) - int(wbaseline[0])) < 19 :
					return {"error":"Baseline range must be equal or greater than 20 years"}
				elif request.query.scenario.lower() == "historical":
					return {"error":"Scenario must be different to historical"}
				else:
					baseFileName = request.query.index.lower()+"_bcsd_historical_"+wgcm
					baseFile = find(baseFileName+"*", folder)
					baselineAvg = calcAvg (baseFile, folder, wbaseline, float(request.query.lat), float(request.query.lon))
					lat = float(request.query.lat)
					lon = float(request.query.lon)
					
					transf = ds.GetGeoTransform()

			px = (lon-transf[0])/transf[1]
			py = (lat-transf[3])/transf[5]

			if wrange and wrange != "false":
				avg = 0
				for band in range( bands ):
					band += 1
					if int(wrange[0]) <= int(band+startDate-1) <= int(wrange[1]):
						srcband = ds.GetRasterBand(band)
						structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
						bandtype = gdal.GetDataTypeName(srcband.DataType)
						intval = struct.unpack(fmttypes[bandtype] , structval)
						if wavg:
							avg += (round((float(intval[0])/100),2))+factor
						else:
							output_item = {'date' : int(band+startDate-1) , 'value' : ((round((float(intval[0])/100),2))+factor)-baselineAvg}
							json_output['values'].append(output_item)
				if avg != 0 and wavg:
					avg = (avg / (int(wrange[1]) - int(wrange[0]) + 1)) - baselineAvg +factor
					output_item = {'date' : 'avg_'+wrange[0]+"-"+wrange[1] , 'value' : str(avg)}
					json_output['values'].append(output_item)
				elif avg == 0 and wavg:
					output_item = {'date' : 'avg_'+wrange[0]+"-"+wrange[1] , 'value' : 'out of range'}
					json_output['values'].append(output_item)
				return json_output

			else:
				for band in range( bands ):
					band += 1
					srcband = ds.GetRasterBand(band)
					structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
					bandtype = gdal.GetDataTypeName(srcband.DataType)
					intval = struct.unpack(fmttypes[bandtype] , structval)
					output_item = {'date' : int(band+startDate-1) , 'value' : ((round((float(intval[0])/100),2))+factor)-baselineAvg}
					json_output['values'].append(output_item)
				return json_output
	else :
		return {"error":"Data not found"}