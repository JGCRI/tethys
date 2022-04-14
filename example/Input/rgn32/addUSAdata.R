
#---------------------------
# Add GCAM USA regions
#---------------------------

library(dplyr); library(data.table); library(metis)

#-------------------------------
# irrigation-frac_gcamUSA.csv
#--------------------------------

df <- data.table::fread("irrigation-fracx.csv",header=T); df
dfUS <- data.table::fread("irrigation-fracx.csv",header=T) %>%
  dplyr::filter(region=="USA"); dfUS
rgnCore <- data.table::fread("RgnNames.csv",header=T) %>%
  dplyr::rename(Region=region_id,region=region); rgnCore
rgnUS <- data.table::fread("RgnNames_gcamUSA.csv",header=T) %>%
  dplyr::rename(Region=region_id,region=region) %>%
  dplyr::filter(!region %in% rgnCore$region); rgnUS

dfUSA <- df
for(i in 1:nrow(rgnUS)){
  df_i <- dfUS %>% dplyr::mutate(Region = rgnUS[i,]$Region, region = rgnUS[i,]$region)
  dfUSA <- dfUSA %>%
    dplyr::bind_rows(df_i)}
dfUSA

data.table::fwrite(x=dfUSA, file="irrigation-frac_gcamUSA.csv")


#--------------------------------------
# Get ratio of basin area by state to basin area in the US
#-----------------------------------
library(metis); library(raster)

# Area of US Basin States
m1 <- metis::mapGCAMBasinsUS52
m2 <- metis::mapUS52
m2 <- sp::spTransform(m2,raster::crs(m1))
mapx<-raster::intersect(m1,m2)
mapx@data <- mapx@data %>%
  dplyr::mutate(subRegion=paste(subRegion.1,subRegion.2,sep="_X_"),
                region=region.1,
                subRegionAlt=paste(subRegionAlt.1,subRegionAlt.2,sep="_X_"),
                subRegionType=paste(subRegionType.1,subRegionType.2,sep="_X_")) %>%
  dplyr::rename(subRegion_GCAMBasin=subRegion.1,
                subRegion_State=subRegion.2,
                subRegionAlt_GCAMBasin=subRegionAlt.1,
                subRegionAlt_State=subRegionAlt.2,
                subRegionType_GCAMBasin=subRegionType.1,
                subRegionType_State=subRegionType.2) %>%
  dplyr::select(-region.1,-region.2)
head(mapx@data)
sp::plot(mapx)
metis.map(dataPolygon=mapx,fillColumn = "subRegion",labels=T,printFig=F)
dfBasinsUS52x <- mapx
dfBasinsUS52x$area_sqkm <- raster::area(dfBasinsUS52x) / 1000000
dfBasinsUS52x@data

# Table with Basin Area, State Area, State-Basin Ratio
df <- dfBasinsUS52x@data %>% 
  dplyr::select(subRegion_GCAMBasin, subRegion_State, area_sqkm_st_basin=area_sqkm) %>%
  dplyr::group_by(subRegion_GCAMBasin) %>% 
  dplyr::mutate(area_sqkm_sum=sum(area_sqkm_st_basin),
                area_ratio = area_sqkm_st_basin/area_sqkm_sum) %>%
  dplyr::ungroup() %>%
  dplyr::left_join(tibble::tribble(
  ~basin, ~subRegion_GCAMBasin ,
  'NelsonR', "Saskatchewan_Nelson",
  'FraserR', "Fraser",
  'MexCstNW', "Mexico_Northwest_Coast",
  'Caribbean', "Caribbean",
  'California', "California_River",
  'MissppRN', "Upper_Mississippi",
  'MissppRS', "Lower_Mississippi_River",
  'UsaColoRN', "Upper_Colorado_River",
  'UsaColoRS', "Lower_Colorado_River", 
  'GreatBasin', "Great",
  'MissouriR', "Missouri_River",
  'ArkWhtRedR', "Arkansas_White_Red",
  'TexasCst', "Texas_Gulf_Coast",
  'UsaCstSE', "South_Atlantic_Gulf",
  'GreatLakes', "Great_Lakes",
  'OhioR', "Ohio_River",
  'UsaPacNW', "Pacific_Northwest",
  'TennR', "Tennessee_River",
  'RioGrande', "Rio_Grande_River",
  'UsaCstNE', "New_England",
  'UsaCstE', "Mid_Atlantic"), by=c("subRegion_GCAMBasin")) %>%
  dplyr::mutate(basin = case_when(is.na(basin)~subRegion_GCAMBasin,
                                      TRUE~basin)); df

data.table::fwrite(x=df, file = "basin_state_area_ratio_gcamUSA.csv")
