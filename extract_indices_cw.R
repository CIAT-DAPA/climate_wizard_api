################
# ClimateWizard
# Author: Jaime Tarapues
# date: 2017
# Data source: NASA Earth Exchange (NEX) Global Daily Downscaled Projections (GDDP)
# Spatial Resolution: 0.25deg x 0.25deg ~ 25x25 km
# Temporal Resolution: Daily from 1950-01-01 00:00:00 to 2100-12-31 11:59:59
################

library(jsonlite)
library(curl)
require(sp)
lon=-76.3 
lat=3.1
yih=1980
yfh=2005
yif=2020
yff=2050
monthly="NO"
# droi=>annual; drof=>monthly
indices =c("cd18", "cdd", "gd10", "tnn", "txx", "tasmax", "tasmin","tas",'hd18','ptot', 'r02', 'sdii')
scenarios = c("historical","rcp45","rcp85") #"historical",
gcmList = c("ensemble","ACCESS1-0", "bcc-csm1-1", "BNU-ESM", "CanESM2", "CCSM4", "CESM1-BGC", "CNRM-CM5", "CSIRO-Mk3-6-0", "GFDL-ESM2G", "GFDL-ESM2M", "inmcm4")


#### Funciones ###
mat <- c()
if(monthly=="YES"){
  mon="&climatology=true" 
}else{mon=NULL}
for (index in indices){
  for (j in c(1:length(scenarios))){
    
    if(scenarios[j]!="historical"){
      period=paste0(yif,'-',yff)
      yi=yif;yf=yff;
    }else{
      period=paste0(yih,'-',yfh)
      yi=yih;yf=yfh;
    }
    for (i in 1:length(gcmList)){
      gcm <- gcmList[i]
      cat(index,scenarios[j],period,gcm)
      data=fromJSON(paste0("http://climatewizard.ccafs-climate.org/service?lat=",lat,"&lon=",lon,"&index=",index,"&scenario=",scenarios[j],"&gcm=",gcm,"&range=",period,"&avg=false",mon))
      out <- data$values
      mat <- rbind(mat,cbind(out,index,scenarios[j],period))
      cat("....done!\n")
    }
    
  }
}
names(mat) <- c("date","Value","Index","scenario","Period")
mat[1:10,]
