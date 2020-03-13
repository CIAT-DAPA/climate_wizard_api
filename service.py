from osgeo import gdal,ogr
from osgeo.gdalconst import *
import struct
import time
import sys,os, fnmatch, os.path
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
import pandas as pd
from pandas import Series, DataFrame, Panel

def find(pattern, path):
    result = []
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            if fnmatch.fnmatch(item, pattern) and item.lower().endswith(".tif"):
                result.append (os.path.join(path, item))
    return result

def calcAvg (file, folder,wrange, lat, lon,wclm,factor):
	name = os.path.basename(file[0])#file.split(folder)
	acroIndex = name.split("_")
	period = acroIndex[4].split("-")
	startDate = int(acroIndex[4].split("-")[0])
	lat = float(lat)
	lon = float(lon)
	ds = gdal.Open(folder+name, GA_ReadOnly)
	transf = ds.GetGeoTransform()

	px = (lon-transf[0])/transf[1]
	py = (lat-transf[3])/transf[5]

	if ds is None:
		return 'Failed open file'
		sys.exit(1)

	bands = ds.RasterCount
	avg = 0
	listwcl=[]
	for band in range( bands ):
		band += 1
		if int(wrange[0]) <= int(band+startDate-1) <= int(wrange[1]):
			srcband = ds.GetRasterBand(band)
			structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
			bandtype = gdal.GetDataTypeName(srcband.DataType)
			intval = struct.unpack(fmttypes[bandtype] , structval)
			avg += round((intval[0]/100.00)+factor,2)
	if avg != 0:
		avg = avg / (int(wrange[1]) - int(wrange[0]) + 1)
	return avg


def bbox_to_pixel_offsets(gt, bbox):
    originX = gt[0]
    originY = gt[3]
    pixel_width = gt[1]
    pixel_height = gt[5]
    x1 = int((bbox[0] - originX) / pixel_width)
    x2 = int((bbox[1] - originX) / pixel_width) + 1

    y1 = int((bbox[3] - originY) / pixel_height)
    y2 = int((bbox[2] - originY) / pixel_height) + 1

    xsize = x2 - x1
    ysize = y2 - y1
    return (x1, y1, xsize, ysize)

	
indexx = {'txavg':'Monthly mean maximum temperatures historical', 'tnavg':'Monthly mean minimum temperatures', 'txx':'Monthly maximum temperatures', 'tnn':'Monthly minimum temperatures', 
'gd10':'growing degree days', 'hd18':'heating degree days', 'cd18':'cooling degree days', 'tx90':'90th percentile Tmax - one value per year', 
'tx90p':'Generalized version: Pct of time T doesnt exceeds ref pd Nth percentile', 'tx10p':'Generalized version: Pct of time T doesnt exceeds ref pd Nth percentile', 
'tn90p':'Generalized version: Pct of time T doesnt exceeds ref pd Nth percentile', 'tn10p':'Generalized version: Pct of time T doesnt exceeds ref pd Nth percentile', 
'fd':'Frost days', 'gsl':'Thermal growing season length', 'hwdi':'Heat wave duration index wrt mean of reference_period', 'ptot':'Monthly total precip', 
'cdd':'Consecutive dry days', 'r02':'Number of wet days > 0.2 mm/d', 'r5d':'Max consec 5 day precip', 'sdii':'simple daily precip intensity index', 'r90p':'calculate of precip due to this too',
'txx1':'Monthly maximum temperatures','txx2':'Monthly maximum temperatures','txx3':'Monthly maximum temperatures','txx4':'Monthly maximum temperatures','txx5':'Monthly maximum temperatures',
'txx6':'Monthly maximum temperatures','txx7':'Monthly maximum temperatures','txx8':'Monthly maximum temperatures','txx9':'Monthly maximum temperatures','txx10':'Monthly maximum temperatures',
'txx11':'Monthly maximum temperatures','txx12':'Monthly maximum temperatures',
'tnn1':'Monthly minimum temperatures','tnn2':'Monthly minimum temperatures','tnn3':'Monthly minimum temperatures','tnn4':'Monthly minimum temperatures','tnn5':'Monthly minimum temperatures',
'tnn6':'Monthly minimum temperatures','tnn7':'Monthly minimum temperatures','tnn8':'Monthly minimum temperatures','tnn9':'Monthly minimum temperatures','tnn10':'Monthly minimum temperatures',
'tnn11':'Monthly minimum temperatures','tnn12':'Monthly minimum temperatures',
'tasmax1':'Monthly mean maximum temperatures','tasmax2':'Monthly mean maximum temperatures','tasmax3':'Monthly mean maximum temperatures','tasmax4':'Monthly mean maximum temperatures','tasmax5':'Monthly mean maximum temperatures',
'tasmax6':'Monthly mean maximum temperatures','tasmax7':'Monthly mean maximum temperatures','tasmax8':'Monthly mean maximum temperatures','tasmax9':'Monthly mean maximum temperatures','tasmax10':'Monthly mean maximum temperatures',
'tasmax11':'Monthly mean maximum temperatures','tasmax12':'Monthly mean maximum temperatures','tasmax':'Mean maximum temperatures',
'tasmin1':'Monthly mean minimum temperatures','tasmin2':'Monthly mean minimum temperatures','tasmin3':'Monthly mean minimum temperatures','tasmin4':'Monthly mean minimum temperatures',
'tasmin5':'Monthly mean minimum temperatures','tasmin6':'Monthly mean minimum temperatures','tasmin7':'Monthly mean minimum temperatures','tasmin8':'Monthly mean minimum temperatures','tasmin9':'Monthly mean minimum temperatures',
'tasmin10':'Monthly mean minimum temperatures','tasmin11':'Monthly mean minimum temperatures','tasmin12':'Monthly mean minimum temperatures','tasmin':'Mean minimum temperatures',
'tas1':'Monthly mean average temperatures','tas2':'Monthly mean average temperatures','tas3':'Monthly mean average temperatures','tas4':'Monthly mean average temperatures','tas5':'Monthly mean average temperatures',
'tas6':'Monthly mean average temperatures','tas7':'Monthly mean average temperatures','tas8':'Monthly mean average temperatures','tas9':'Monthly mean average temperatures','tas10':'Monthly mean average temperatures',
'tas11':'Monthly mean average temperatures','tas12':'Monthly mean average temperatures','tas':'Mean average temperatures',
'pr1':'Monthly accumulated precipitation','pr2':'Monthly accumulated precipitation','pr3':'Monthly accumulated precipitation','pr4':'Monthly accumulated precipitation','pr5':'Monthly accumulated precipitation',
'pr6':'Monthly accumulated precipitation','pr7':'Monthly accumulated precipitation','pr8':'Monthly accumulated precipitation','pr9':'Monthly accumulated precipitation','pr10':'Monthly accumulated precipitation',
'pr11':'Monthly accumulated precipitation','pr12':'Monthly accumulated precipitation','pr':'Accumulated precipitation',
'sdii1':'Monthly simple daily precipitation intensity index','sdii2':'Monthly simple daily precipitation intensity index','sdii3':'Monthly simple daily precipitation intensity index','sdii4':'Monthly simple daily precipitation intensity index',
'sdii5':'Monthly simple daily precipitation intensity index','sdii6':'Monthly simple daily precipitation intensity index','sdii7':'Monthly simple daily precipitation intensity index','sdii8':'Monthly simple daily precipitation intensity index',
'sdii9':'Monthly simple daily precipitation intensity index','sdii10':'Monthly simple daily precipitation intensity index','sdii11':'Monthly simple daily precipitation intensity index','sdii12':'Monthly simple daily precipitation intensity index',
'r021':'Monthly number of wet days > 0.2 mm/day','r022':'Monthly number of wet days > 0.2 mm/day','r023':'Monthly number of wet days > 0.2 mm/day','r024':'Monthly number of wet days > 0.2 mm/day',
'r025':'Monthly number of wet days > 0.2 mm/day','r026':'Monthly number of wet days > 0.2 mm/day','r027':'Monthly number of wet days > 0.2 mm/day','r028':'Monthly number of wet days > 0.2 mm/day','r029':'Monthly number of wet days > 0.2 mm/day',
'r0210':'Monthly number of wet days > 0.2 mm/day','r0211':'Monthly number of wet days > 0.2 mm/day','r0212':'Monthly number of wet days > 0.2 mm/day','tdjf':'Mean temperatures for DJF season'}

fmttypes = {'Byte':'B', 'UInt16':'H', 'Int16':'h', 'UInt32':'I', 
            'Int32':'i', 'Float32':'f', 'Float64':'d'}	

@get('/service')
def service():

	lat =float(request.query.lat) #3#sys.argv[1]
	lon =float(request.query.lon)  #-76#sys.argv[2]
	scenario=request.query.scenario#"rcp45"
	gcm=request.query.gcm#"ACCESS1-0"
	avg=request.query.avg#'false'
	climatology=request.query.climatology#'true'
	index=request.query.index#"tas"
	geojson=request.query.geojson#None
	baseline=request.query.baseline#"1980-2000"#None #
	stats=request.query.stats#None
	rangee=request.query.range#"2041-2060"# "true"# None #
				
	if not baseline or baseline=="false":
		brange = ["1950","2005"]
	else:
		brange = baseline.split("-")	
		if int(brange[1]) >2005:
			brange[1]="2005"	
		
	if not rangee:
		if scenario.lower() == "historical":
			wrange = ["1976","2005"]
		else:
			wrange = ["2040","2069"]
	elif rangee == "false":
		wrange = "false"
	else:
		if scenario.lower() == "historical":
			wrange = brange
		else:
			wrange = rangee.split("-")

		
	if not gcm:
		wgcm = "ensemble_lowest"
	else:
		wgcm = gcm.lower()

	if not avg or avg == "true":
		wavg = True
	else:
		wavg = False

	if climatology == "true":
		wclm = True
	else:
		wclm = False

	# for convert to celsius
	if index.lower()=="txavg" or index.lower()=="tnavg" or index.lower()=="txx" or index.lower()=="tnn" or index.lower()=="tas" or index.lower()=="tasmin" or index.lower()=="tasmax" or index[0:3].lower()=="tas":
		factor=-273.15 
	else:
		factor=0

	fileName = index.lower()+"_bcsd_"+scenario.lower()+"_"+wgcm
	folderModels = "/mnt/data_climatewizard/AR5_Global_Daily_25k/out_stats_tiff/"
	folder = folderModels+wgcm+"/"


	if wclm:
		fileNameH = index.lower()+"_bcsd_historical_"+wgcm
		folder = folder + "split/"
		allfilesH = find(fileNameH+"*", folder)
		listwclH=[]	
		if len(allfilesH) > 0:
			if wclm:
				for nameFile in allfilesH:	
					basenamefile= os.path.basename(nameFile)
					acroIndex = basenamefile.split("_")	
					period = acroIndex[4].split("-")
					startDate = int(period[0])	
					endDate = int(period[1])				
						
					if (int(brange[1]) - int(brange[0])) < 19 :
						return "error Baseline range must be equal or greater than 20 years"
						sys.exit(1)
					# print wrange				
					# print baseline,rangee,wrange, startDate
					basenamefile= os.path.basename(nameFile)
					ds = gdal.Open(nameFile, GA_ReadOnly)
					transf = ds.GetGeoTransform()

					px = (lon-transf[0])/transf[1]
					py = (lat-transf[3])/transf[5]

					if ds is None:
						return 'Failed open file'
						sys.exit(1)

					bands = ds.RasterCount
					avg = 0

					for band in range( bands ):
						band += 1
						if int(brange[0]) <= int(band+startDate-1) <= int(brange[1]):
							srcband = ds.GetRasterBand(band)
							structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
							bandtype = gdal.GetDataTypeName(srcband.DataType)
							intval = struct.unpack(fmttypes[bandtype] , structval)
							if wclm:
								# print round((float(intval[0])/100.00)+factor,2),int(band+startDate-1)
								listwclH.append(round((intval[0]/100.00)+factor,2))

	allfiles = find(fileName+"*", folder)
	output_item = ""
	listfut=[]
	listfutanual=[]
	if len(allfiles) > 0:
		json_output = {'name' : indexx[index.lower()], 'acronym':index,'model':wgcm,'scenario':scenario.lower() ,'values':[]}
		listwcl=[]

		for nameFile in allfiles:
			monthlyYear = 0
			name = os.path.basename(nameFile)
			acroIndex = name.split("_")
			period = acroIndex[4].split("-")
			startDate = int(period[0])
			# endDate = int(period[1])
			if rangee=="true" or rangee=="false":
				wrange=(acroIndex[4].split(".")[0]).split("-")
				
			ds = gdal.Open(nameFile, GA_ReadOnly)
			if ds is None:
					return 'Failed open file'
					sys.exit(1)
			bands = ds.RasterCount

			if geojson:
				file = '/tmp/cwizard'+time.strftime("%H:%M:%S")+'.geojson'
				# return file
				with open(file, 'w') as file_:
					file_.write(geojson)

				if stats:
					tstats = stats.split(",")
					rstats = []
					for stat in tstats:
						rstats.append(stat)
				else :
					rstats = ['min', 'max', 'median', 'mean','percentile_5','percentile_25','percentile_75','percentile_95']

				# vector_path=file
				# raster_path=nameFile
				# nodata_value=-9999
				# global_src_extent=False						
				# rds = gdal.Open(raster_path, GA_ReadOnly)
				# assert(rds)
				# bands = rds.RasterCount
				# stats = []
				
				# vds = ogr.Open(vector_path, GA_ReadOnly)  # TODO maybe open update if we want to write stats
				# assert(vds)
				# vlyr = vds.GetLayer(0)		
				# mem_drv = ogr.GetDriverByName('Memory')
				# driver = gdal.GetDriverByName('MEM')

				# feat = vlyr.GetNextFeature()
				
				# mem_ds = mem_drv.CreateDataSource('out')
				# mem_layer = mem_ds.CreateLayer('poly', None, ogr.wkbPolygon)
				# mem_layer.CreateFeature(feat.Clone())				
				
				for band in range( bands ):
					band += 1
					if wclm:
						if int(wrange[0]) <= int(monthlyYear+startDate) <= int(wrange[1]):
							with fiona.open(file) as src:
								zs = zonal_stats(src, nameFile, band=band,stats=rstats)
							json_output['values'].append({'date' : str(int(monthlyYear+startDate))+"-"+str(int(((band-1)%12)+1)) , 'value' : zs[0]})
						if (band % 12) == 0:
							monthlyYear += 1
					else:
						# print file,nameFile, band,rstats
						if int(wrange[0]) <= int(band+startDate-1) <= int(wrange[1]):
							# print "hola"
							# with fiona.open(file) as src:
								
								# zs = zonal_stats(src, nameFile, band=band,stats=rstats)
							zs = zonal_stats(file, nameFile, band=band,stats=rstats,all_touched=True) #
							ordStats=[]
							for stator in rstats:
								ordStats.append(stator+": "+str(round(zs[0][stator],2)))							
							json_output['values'].append({'date' : int(band+startDate-1) , 'value' : ordStats})


							# rb = rds.GetRasterBand(band)
							# rgt = rds.GetGeoTransform()
							# if nodata_value:
								# nodata_value = float(nodata_value)
								# rb.SetNoDataValue(nodata_value)
							
							# if not global_src_extent:
								# src_offset = bbox_to_pixel_offsets(rgt, feat.geometry().GetEnvelope())
								# src_array = rb.ReadAsArray(*src_offset)

								# new_gt = (
									# (rgt[0] + (src_offset[0] * rgt[1])),
									# rgt[1],
									# 0.0,
									# (rgt[3] + (src_offset[1] * rgt[5])),
									# 0.0,
									# rgt[5]
								# )

							# rvds = driver.Create('', src_offset[2], src_offset[3], 1, gdal.GDT_Byte)
							# rvds.SetGeoTransform(new_gt)
							# gdal.RasterizeLayer(rvds, [1], mem_layer, burn_values=[1])
							# rv_array = rvds.ReadAsArray()	

							# masked = np.ma.MaskedArray(
								# src_array,
								# mask=np.logical_or(
									# src_array == nodata_value,
									# np.logical_not(rv_array)
								# )
							# )
							# factor=0
							# feature_stats = {
								# 'min': round((float(masked.min())/100.00)+factor,2),
								# 'mean': round((float(masked.mean())/100.00)+factor,2),
								# 'max': round((float(masked.max())/100.00)+factor,2),
								# 'std': round((float(masked.std())/100.00)+factor,2),
								# 'sum': round((float(masked.sum())/100.00)+factor,2),
								# 'median': round((float(np.median(masked))/100.00)+factor,2),
								# 'per5': round((float(np.percentile(masked, 5))/100.00)+factor,2),
								# 'per25': round((float(np.percentile(masked, 25))/100.00)+factor,2),
								# 'per75': round((float(np.percentile(masked, 75))/100.00)+factor,2),
								# 'per95': round((float(np.percentile(masked, 95))/100.00)+factor,2),
								# 'count': int(masked.count())
							# }
							# json_output['values'].append({'date' : int(band+startDate-1) , 'value' : feature_stats})	
							# json_output['values'].append({'date' : int(band+startDate-1) , 'value' : "hola"})	
			else:

				baseFileName = index.lower()+"_bcsd_historical_"+wgcm
				baseFile = find(baseFileName+"*", folder)		
				baselineAvg = 0
				if not baseline or baseline =="false": # and wclm==False
					name = os.path.basename(baseFile[0])#file.split(folder)
					acroIndex = name.split("_")				
					wbaseline = (acroIndex[4].split(".")[0]).split("-")
				else:
					wbaseline = brange#baseline.split("-")
					if (int(wbaseline[1]) - int(wbaseline[0])) < 19 :
						return "error Baseline range must be equal or greater than 20 years"
					elif scenario.lower() == "historical":
						return "error Scenario must be different to historical"
					# else:

				if wavg:
					baselineAvg = calcAvg (baseFile, folder, wbaseline, float(lat), float(lon),wclm,factor)
				elif not wavg and not wclm and baseline or baseline=="true": 
					baselineAvganual = calcAvg (baseFile, folder, wbaseline, float(lat), float(lon),wclm,factor)
					
				lat = float(lat)
				lon = float(lon)
				
				transf = ds.GetGeoTransform()

				px = (lon-transf[0])/transf[1]
				py = (lat-transf[3])/transf[5]

				if wrange and wrange != "false":
					
					avg = 0

					for band in range( bands ):
						band += 1
						if wclm:
							if int(wrange[0]) <= int(monthlyYear+startDate) <= int(wrange[1]):
								srcband = ds.GetRasterBand(band)
								structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
								bandtype = gdal.GetDataTypeName(srcband.DataType)
								intval = struct.unpack(fmttypes[bandtype] , structval)
								if wavg:
									# avg += round((float(intval[0])/100.00)+factor,2)
									avg =1
									valuei=round((intval[0]/100.00)+factor,2)
									listwcl.append(valuei)
								elif not baseline or baseline=="false":
									output_item = {'date' : str(int(monthlyYear+startDate))+"-"+str(int(((band-1)%12)+1)) , 'value' : (round(((((intval[0]/100.00))+factor)-baselineAvg),2))}
									json_output['values'].append(output_item)
								listfut.append(round(((intval[0]/100.00))+factor,2))
							if (band % 12) == 0:
								monthlyYear += 1
						else:
							
							if int(wrange[0]) <= int(band+startDate-1) <= int(wrange[1]):
								srcband = ds.GetRasterBand(band)
								structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
								bandtype = gdal.GetDataTypeName(srcband.DataType)
								intval = struct.unpack(fmttypes[bandtype] , structval)
								if wavg and baseline!="false":
									
									avg += round((intval[0]/100.00)+factor,2)
									# print avg,(float(intval[0])/100.00)+factor #str(band)+'\t'+
								elif baseline!="false" and wclm:
									output_item = {'date' : int(band+startDate-1) , 'value' : (round(((((intval[0]/100.00))+factor)-baselineAvg),2))}
									json_output['values'].append(output_item)
								elif baseline=="false" and wavg and not wclm:	
									output_item = {'date' : int(band+startDate-1) , 'value' : (round(((((intval[0]/100.00))+factor)),2))}
									json_output['values'].append(output_item)	
								elif wavg==False and not baseline and wclm==False:
									output_item = {'date' : int(band+startDate-1) , 'value' : round((intval[0]/100.00)+factor,2)}
									json_output['values'].append(output_item)	
									
								listfutanual.append(round(((intval[0]/100.00))+factor,2))	
								
					if avg != 0 and wavg and not wclm:

						# print avg,wrange,baselineAvg,(int(wrange[1]) - int(wrange[0]) + 1)
						avg = round((avg / (int(wrange[1]) - int(wrange[0]) + 1)) - baselineAvg,2)
						output_item = {'date' : 'avg_'+wrange[0]+"-"+wrange[1] , 'value' : str(avg)}
						json_output['values'].append(output_item)
					elif avg == 0 and wavg and wclm==False and baseline!="false":
						output_item = {'date' : 'avg_'+wrange[0]+"-"+wrange[1] , 'value' : 'out of range'}
						json_output['values'].append(output_item)
				



				else:
					
					for band in range( bands ):
						band += 1
						srcband = ds.GetRasterBand(band)
						structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
						bandtype = gdal.GetDataTypeName(srcband.DataType)
						intval = struct.unpack(fmttypes[bandtype] , structval)
						if wclm:
							output_item = {'date' : str(int(monthlyYear+startDate))+"-"+str(int(((band-1)%12)+1)) , 'value' : (round(((((intval[0]/100.00))+factor)-baselineAvg),2))}
							if (band % 12) == 0:
								monthlyYear += 1
						else: 
							output_item = {'date' : int(band+startDate-1) , 'value' : (round(((((intval[0]/100.00))+factor)-baselineAvg),2))}
						json_output['values'].append(output_item)
					# print json_output
					

		if wavg and wclm and not geojson:
			nao=np.array(listwcl)
			dates_nao = pd.date_range(wrange[0], periods=nao.shape[0], freq='M')
			AO = Series(nao, index=dates_nao)
			aonao = pd.DataFrame()#{'NAO' : nao}
			aonao[scenario] = AO.groupby([AO.index.month]).mean() 		## aonao = AO.resample("M").mean() #aonao['NAO']
			naoH=np.array(listwclH)
			dates_naoH = pd.date_range(wbaseline[0], periods=naoH.shape[0], freq='M')
			AOH = Series(naoH, index=dates_naoH)	
			aonao["historicalH"] = AOH.groupby([AOH.index.month]).mean()
			# if index.lower()=="txavg" or index.lower()=="tnavg" or index.lower()=="txx" or index.lower()=="tnn" or index.lower()=="tas" or index.lower()=="tasmin" or index.lower()=="tasmax":

			if not baseline or len(baseline.split("-"))>1:
				aonao["delta"] = aonao[scenario]-aonao["historicalH"]
				output_item = {'date' : range(1,13) , 'value' : np.round(aonao["delta"],2).tolist()} # delta
				json_output['values'].append(output_item)

			else:
				if scenario=="historical":
					output_item = {'date' : range(1,13) , 'value' : np.round(aonao["historical"],2).tolist()}
					json_output['values'].append(output_item)
				else:
					output_item = {'date' : range(1,13) , 'value' : np.round(aonao[scenario],2).tolist()}
					json_output['values'].append(output_item)	
					
		if wclm and baseline!="false" and not wavg and not geojson:
			
			nao=np.array(listwclH)
			dates_nao = pd.date_range(brange[0], periods=nao.shape[0], freq='M')
			AO = Series(nao, index=dates_nao)	
			fut=np.array(listfut)
			dates_fut = pd.date_range(wrange[0], periods=fut.shape[0], freq='M')
			AOfut = Series(fut, index=dates_fut)			
			datamon = pd.DataFrame()#{'NAO' : nao}
			calmon=AO.groupby([AO.index.month]).mean() 
			datamon['hist']=np.tile(calmon,(int(wrange[1])-int(wrange[0])+1))
			datamon[scenario]=fut
			datamon["delta"] = datamon[scenario]-datamon["hist"]
			datamon["dates"] =pd.Series(dates_fut.format())
			# output_item = {'date' : (u", ".join(dates_fut.strftime("%Y-%m-%d"))), 'value' : } #dates_fut.strftime("%Y-%m-%d")

			output_item = {'date' :datamon["dates"].tolist(), 'value' :np.round(datamon["delta"],2).tolist() } #dates_fut.strftime("%Y-%m-%d")
			json_output['values'].append(output_item)
			# print json_output
			# print listfut,listwclH
		elif not geojson and not wavg and not wclm and baseline or baseline=="true":  

			output_item = {'date' :range(int(wrange[0]),int(wrange[1])+1), 'value' :np.round(np.array(listfutanual)-baselineAvganual,2).tolist()} #dates_fut.strftime("%Y-%m-%d")
			json_output['values'].append(output_item)		
		return json_output	
	else:
		return "error Data not found"
		

@post('/service')
def do_service():

	lat =float(request.query.lat) #3#sys.argv[1]
	lon =float(request.query.lon)  #-76#sys.argv[2]
	scenario=request.query.scenario#"rcp45"
	gcm=request.query.gcm#"ACCESS1-0"
	avg=request.query.avg#'false'
	climatology=request.query.climatology#'true'
	index=request.query.index#"tas"
	geojson=request.query.geojson#None
	baseline=request.query.baseline#"1980-2000"#None #
	stats=request.query.stats#None
	rangee=request.query.range#"2041-2060"# "true"# None #
				
	if not baseline or baseline=="false":
		brange = ["1950","2005"]
	else:
		brange = baseline.split("-")	
		if int(brange[1]) >2005:
			brange[1]="2005"	
		
	if not rangee:
		if scenario.lower() == "historical":
			wrange = ["1976","2005"]
		else:
			wrange = ["2040","2069"]
	elif rangee == "false":
		wrange = "false"
	else:
		if scenario.lower() == "historical":
			wrange = brange
		else:
			wrange = rangee.split("-")

		
	if not gcm:
		wgcm = "ensemble_lowest"
	else:
		wgcm = gcm.lower()

	if not avg or avg == "true":
		wavg = True
	else:
		wavg = False

	if climatology == "true":
		wclm = True
	else:
		wclm = False

	# for convert to celsius
	if index.lower()=="txavg" or index.lower()=="tnavg" or index.lower()=="txx" or index.lower()=="tnn" or index.lower()=="tas" or index.lower()=="tasmin" or index.lower()=="tasmax" or index[0:3].lower()=="tas":
		factor=-273.15 
	else:
		factor=0

	fileName = index.lower()+"_bcsd_"+scenario.lower()+"_"+wgcm
	folderModels = "/mnt/data_climatewizard/AR5_Global_Daily_25k/out_stats_tiff/"
	folder = folderModels+wgcm+"/"


	if wclm:
		fileNameH = index.lower()+"_bcsd_historical_"+wgcm
		folder = folder + "split/"
		allfilesH = find(fileNameH+"*", folder)
		listwclH=[]	
		if len(allfilesH) > 0:
			if wclm:
				for nameFile in allfilesH:	
					basenamefile= os.path.basename(nameFile)
					acroIndex = basenamefile.split("_")	
					period = acroIndex[4].split("-")
					startDate = int(period[0])	
					endDate = int(period[1])				
						
					if (int(brange[1]) - int(brange[0])) < 19 :
						return "error Baseline range must be equal or greater than 20 years"
						sys.exit(1)
					# print wrange				
					# print baseline,rangee,wrange, startDate
					basenamefile= os.path.basename(nameFile)
					ds = gdal.Open(nameFile, GA_ReadOnly)
					transf = ds.GetGeoTransform()

					px = (lon-transf[0])/transf[1]
					py = (lat-transf[3])/transf[5]

					if ds is None:
						return 'Failed open file'
						sys.exit(1)

					bands = ds.RasterCount
					avg = 0

					for band in range( bands ):
						band += 1
						if int(brange[0]) <= int(band+startDate-1) <= int(brange[1]):
							srcband = ds.GetRasterBand(band)
							structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
							bandtype = gdal.GetDataTypeName(srcband.DataType)
							intval = struct.unpack(fmttypes[bandtype] , structval)
							if wclm:
								# print round((float(intval[0])/100.00)+factor,2),int(band+startDate-1)
								listwclH.append(round((intval[0]/100.00)+factor,2))

	allfiles = find(fileName+"*", folder)
	output_item = ""
	listfut=[]
	listfutanual=[]
	if len(allfiles) > 0:
		json_output = {'name' : indexx[index.lower()], 'acronym':index,'model':wgcm,'scenario':scenario.lower() ,'values':[]}
		listwcl=[]

		for nameFile in allfiles:
			monthlyYear = 0
			name = os.path.basename(nameFile)
			acroIndex = name.split("_")
			period = acroIndex[4].split("-")
			startDate = int(period[0])
			# endDate = int(period[1])
			if rangee=="true" or rangee=="false":
				wrange=(acroIndex[4].split(".")[0]).split("-")
				
			ds = gdal.Open(nameFile, GA_ReadOnly)
			if ds is None:
					return 'Failed open file'
					sys.exit(1)
			bands = ds.RasterCount

			if geojson:
				file = '/tmp/cwizard'+time.strftime("%H:%M:%S")+'.geojson'
				# return file
				with open(file, 'w') as file_:
					file_.write(geojson)

				if stats:
					tstats = stats.split(",")
					rstats = []
					for stat in tstats:
						rstats.append(stat)
				else :
					rstats = ['min', 'max', 'median', 'mean','percentile_5','percentile_25','percentile_75','percentile_95']

				# vector_path=file
				# raster_path=nameFile
				# nodata_value=-9999
				# global_src_extent=False						
				# rds = gdal.Open(raster_path, GA_ReadOnly)
				# assert(rds)
				# bands = rds.RasterCount
				# stats = []
				
				# vds = ogr.Open(vector_path, GA_ReadOnly)  # TODO maybe open update if we want to write stats
				# assert(vds)
				# vlyr = vds.GetLayer(0)		
				# mem_drv = ogr.GetDriverByName('Memory')
				# driver = gdal.GetDriverByName('MEM')

				# feat = vlyr.GetNextFeature()
				
				# mem_ds = mem_drv.CreateDataSource('out')
				# mem_layer = mem_ds.CreateLayer('poly', None, ogr.wkbPolygon)
				# mem_layer.CreateFeature(feat.Clone())				
				
				for band in range( bands ):
					band += 1
					if wclm:
						if int(wrange[0]) <= int(monthlyYear+startDate) <= int(wrange[1]):
							with fiona.open(file) as src:
								zs = zonal_stats(src, nameFile, band=band,stats=rstats)
							json_output['values'].append({'date' : str(int(monthlyYear+startDate))+"-"+str(int(((band-1)%12)+1)) , 'value' : zs[0]})
						if (band % 12) == 0:
							monthlyYear += 1
					else:
						# print file,nameFile, band,rstats
						if int(wrange[0]) <= int(band+startDate-1) <= int(wrange[1]):
							# print "hola"
							# with fiona.open(file) as src:
								
								# zs = zonal_stats(src, nameFile, band=band,stats=rstats)
							zs = zonal_stats(file, nameFile, band=band,stats=rstats,all_touched=True) #
							ordStats=[]
							for stator in rstats:
								ordStats.append(stator+": "+str(round(zs[0][stator],2)))							
							json_output['values'].append({'date' : int(band+startDate-1) , 'value' : ordStats})


							# rb = rds.GetRasterBand(band)
							# rgt = rds.GetGeoTransform()
							# if nodata_value:
								# nodata_value = float(nodata_value)
								# rb.SetNoDataValue(nodata_value)
							
							# if not global_src_extent:
								# src_offset = bbox_to_pixel_offsets(rgt, feat.geometry().GetEnvelope())
								# src_array = rb.ReadAsArray(*src_offset)

								# new_gt = (
									# (rgt[0] + (src_offset[0] * rgt[1])),
									# rgt[1],
									# 0.0,
									# (rgt[3] + (src_offset[1] * rgt[5])),
									# 0.0,
									# rgt[5]
								# )

							# rvds = driver.Create('', src_offset[2], src_offset[3], 1, gdal.GDT_Byte)
							# rvds.SetGeoTransform(new_gt)
							# gdal.RasterizeLayer(rvds, [1], mem_layer, burn_values=[1])
							# rv_array = rvds.ReadAsArray()	

							# masked = np.ma.MaskedArray(
								# src_array,
								# mask=np.logical_or(
									# src_array == nodata_value,
									# np.logical_not(rv_array)
								# )
							# )
							# factor=0
							# feature_stats = {
								# 'min': round((float(masked.min())/100.00)+factor,2),
								# 'mean': round((float(masked.mean())/100.00)+factor,2),
								# 'max': round((float(masked.max())/100.00)+factor,2),
								# 'std': round((float(masked.std())/100.00)+factor,2),
								# 'sum': round((float(masked.sum())/100.00)+factor,2),
								# 'median': round((float(np.median(masked))/100.00)+factor,2),
								# 'per5': round((float(np.percentile(masked, 5))/100.00)+factor,2),
								# 'per25': round((float(np.percentile(masked, 25))/100.00)+factor,2),
								# 'per75': round((float(np.percentile(masked, 75))/100.00)+factor,2),
								# 'per95': round((float(np.percentile(masked, 95))/100.00)+factor,2),
								# 'count': int(masked.count())
							# }
							# json_output['values'].append({'date' : int(band+startDate-1) , 'value' : feature_stats})	
							# json_output['values'].append({'date' : int(band+startDate-1) , 'value' : "hola"})	
			else:

				baseFileName = index.lower()+"_bcsd_historical_"+wgcm
				baseFile = find(baseFileName+"*", folder)		
				baselineAvg = 0
				if not baseline or baseline =="false": # and wclm==False
					name = os.path.basename(baseFile[0])#file.split(folder)
					acroIndex = name.split("_")				
					wbaseline = (acroIndex[4].split(".")[0]).split("-")
				else:
					wbaseline = brange#baseline.split("-")
					if (int(wbaseline[1]) - int(wbaseline[0])) < 19 :
						return "error Baseline range must be equal or greater than 20 years"
					elif scenario.lower() == "historical":
						return "error Scenario must be different to historical"
					# else:

				if wavg:
					baselineAvg = calcAvg (baseFile, folder, wbaseline, float(lat), float(lon),wclm,factor)
				elif not wavg and not wclm and baseline or baseline=="true": 
					baselineAvganual = calcAvg (baseFile, folder, wbaseline, float(lat), float(lon),wclm,factor)
					
				lat = float(lat)
				lon = float(lon)
				
				transf = ds.GetGeoTransform()

				px = (lon-transf[0])/transf[1]
				py = (lat-transf[3])/transf[5]

				if wrange and wrange != "false":
					
					avg = 0

					for band in range( bands ):
						band += 1
						if wclm:
							if int(wrange[0]) <= int(monthlyYear+startDate) <= int(wrange[1]):
								srcband = ds.GetRasterBand(band)
								structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
								bandtype = gdal.GetDataTypeName(srcband.DataType)
								intval = struct.unpack(fmttypes[bandtype] , structval)
								if wavg:
									# avg += round((float(intval[0])/100.00)+factor,2)
									avg =1
									valuei=round((intval[0]/100.00)+factor,2)
									listwcl.append(valuei)
								elif not baseline or baseline=="false":
									output_item = {'date' : str(int(monthlyYear+startDate))+"-"+str(int(((band-1)%12)+1)) , 'value' : (round(((((intval[0]/100.00))+factor)-baselineAvg),2))}
									json_output['values'].append(output_item)
								listfut.append(round(((intval[0]/100.00))+factor,2))
							if (band % 12) == 0:
								monthlyYear += 1
						else:
							
							if int(wrange[0]) <= int(band+startDate-1) <= int(wrange[1]):
								srcband = ds.GetRasterBand(band)
								structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
								bandtype = gdal.GetDataTypeName(srcband.DataType)
								intval = struct.unpack(fmttypes[bandtype] , structval)
								if wavg and baseline!="false":
									
									avg += round((intval[0]/100.00)+factor,2)
									# print avg,(float(intval[0])/100.00)+factor #str(band)+'\t'+
								elif baseline!="false" and wclm:
									output_item = {'date' : int(band+startDate-1) , 'value' : (round(((((intval[0]/100.00))+factor)-baselineAvg),2))}
									json_output['values'].append(output_item)
								elif baseline=="false" and wavg and not wclm:	
									output_item = {'date' : int(band+startDate-1) , 'value' : (round(((((intval[0]/100.00))+factor)),2))}
									json_output['values'].append(output_item)	
								elif wavg==False and not baseline and wclm==False:
									output_item = {'date' : int(band+startDate-1) , 'value' : round((intval[0]/100.00)+factor,2)}
									json_output['values'].append(output_item)	
									
								listfutanual.append(round(((intval[0]/100.00))+factor,2))	
								
					if avg != 0 and wavg and not wclm:

						# print avg,wrange,baselineAvg,(int(wrange[1]) - int(wrange[0]) + 1)
						avg = round((avg / (int(wrange[1]) - int(wrange[0]) + 1)) - baselineAvg,2)
						output_item = {'date' : 'avg_'+wrange[0]+"-"+wrange[1] , 'value' : str(avg)}
						json_output['values'].append(output_item)
					elif avg == 0 and wavg and wclm==False and baseline!="false":
						output_item = {'date' : 'avg_'+wrange[0]+"-"+wrange[1] , 'value' : 'out of range'}
						json_output['values'].append(output_item)
				



				else:
					
					for band in range( bands ):
						band += 1
						srcband = ds.GetRasterBand(band)
						structval = srcband.ReadRaster(int(px), int(py), 1, 1, buf_type=srcband.DataType )
						bandtype = gdal.GetDataTypeName(srcband.DataType)
						intval = struct.unpack(fmttypes[bandtype] , structval)
						if wclm:
							output_item = {'date' : str(int(monthlyYear+startDate))+"-"+str(int(((band-1)%12)+1)) , 'value' : (round(((((intval[0]/100.00))+factor)-baselineAvg),2))}
							if (band % 12) == 0:
								monthlyYear += 1
						else: 
							output_item = {'date' : int(band+startDate-1) , 'value' : (round(((((intval[0]/100.00))+factor)-baselineAvg),2))}
						json_output['values'].append(output_item)
					# print json_output
					

		if wavg and wclm and not geojson:
			nao=np.array(listwcl)
			dates_nao = pd.date_range(wrange[0], periods=nao.shape[0], freq='M')
			AO = Series(nao, index=dates_nao)
			aonao = pd.DataFrame()#{'NAO' : nao}
			aonao[scenario] = AO.groupby([AO.index.month]).mean() 		## aonao = AO.resample("M").mean() #aonao['NAO']
			naoH=np.array(listwclH)
			dates_naoH = pd.date_range(wbaseline[0], periods=naoH.shape[0], freq='M')
			AOH = Series(naoH, index=dates_naoH)	
			aonao["historicalH"] = AOH.groupby([AOH.index.month]).mean()
			# if index.lower()=="txavg" or index.lower()=="tnavg" or index.lower()=="txx" or index.lower()=="tnn" or index.lower()=="tas" or index.lower()=="tasmin" or index.lower()=="tasmax":

			if not baseline or len(baseline.split("-"))>1:
				aonao["delta"] = aonao[scenario]-aonao["historicalH"]
				output_item = {'date' : range(1,13) , 'value' : np.round(aonao["delta"],2).tolist()} # delta
				json_output['values'].append(output_item)

			else:
				if scenario=="historical":
					output_item = {'date' : range(1,13) , 'value' : np.round(aonao["historical"],2).tolist()}
					json_output['values'].append(output_item)
				else:
					output_item = {'date' : range(1,13) , 'value' : np.round(aonao[scenario],2).tolist()}
					json_output['values'].append(output_item)	
					
		if wclm and baseline!="false" and not wavg and not geojson:
			
			nao=np.array(listwclH)
			dates_nao = pd.date_range(brange[0], periods=nao.shape[0], freq='M')
			AO = Series(nao, index=dates_nao)	
			fut=np.array(listfut)
			dates_fut = pd.date_range(wrange[0], periods=fut.shape[0], freq='M')
			AOfut = Series(fut, index=dates_fut)			
			datamon = pd.DataFrame()#{'NAO' : nao}
			calmon=AO.groupby([AO.index.month]).mean() 
			datamon['hist']=np.tile(calmon,(int(wrange[1])-int(wrange[0])+1))
			datamon[scenario]=fut
			datamon["delta"] = datamon[scenario]-datamon["hist"]
			datamon["dates"] =pd.Series(dates_fut.format())
			# output_item = {'date' : (u", ".join(dates_fut.strftime("%Y-%m-%d"))), 'value' : } #dates_fut.strftime("%Y-%m-%d")

			output_item = {'date' :datamon["dates"].tolist(), 'value' :np.round(datamon["delta"],2).tolist() } #dates_fut.strftime("%Y-%m-%d")
			json_output['values'].append(output_item)
			# print json_output
			# print listfut,listwclH
		elif not geojson and not wavg and not wclm and baseline or baseline=="true":  

			output_item = {'date' :range(int(wrange[0]),int(wrange[1])+1), 'value' :np.round(np.array(listfutanual)-baselineAvganual,2).tolist()} #dates_fut.strftime("%Y-%m-%d")
			json_output['values'].append(output_item)		
		return json_output	
	else:
		return "error Data not found"
	
# return range(10)
# sys.exit(0)

# http://earthpy.org/pandas-basics.html
# http://benalexkeen.com/resampling-time-series-data-with-pandas/