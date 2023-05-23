# Food Twin
Work Related to a proof of concept Food System Digital Twin. Connected to [the Plotline](https://theplotline.org/).


|Data Name|Path|Description|Source|
|---------|----|-----------|------|
|cdl_codes|input-data/cdl-codes.csv|This table has all the codes used in the Cropscape data with the class name and color alongside the code.|[https://www.nass.usda.gov/Research_and_Science/Cropland/docs/CDL_codes_names_colors.xls](https://www.nass.usda.gov/Research_and_Science/Cropland/docs/CDL_codes_names_colors.xls)|
|county_crops|input-data/county-crops-conus-all.csv|This is a table of all US counties joined with zonal histograms of cropscape data. The result is a dataframe of all counties with the number of pixels of each cdl_code that is in each county.|Zonal histogram|
|state_fp_codes|input-data/state-fp-codes.csv|List of FIP codes by state. This is used to help with geographic data joins.|[https://www.bls.gov/respondents/mwr/electronic-data-interchange/appendix-d-usps-state-abbreviations-and-fips-codes.htm](https://www.bls.gov/respondents/mwr/electronic-data-interchange/appendix-d-usps-state-abbreviations-and-fips-codes.htm)|
|scd_calories|input-data/stability_crop_diversity.csv|Data generated in the study, Divergent impacts of crop diversity on caloric and economic yield stability, (DOI: 10.1088/1748-9326/aca2be). We use their Clean_Data.csv which is a list of calories of crops produced by state. Eventually this is what is used to convert the pixels of production to calories of production|[https://doi.org/10.5281/zenodo.7332106](https://doi.org/10.5281/zenodo.7332106)|
|cdl_scd_crosswalk|input-data/crosswalk-cdl<>stability-crop-diversity.csv|This dataset is what we use to crosswalk cdl_codes to the crop names in stablity crop diversity study data|Done by hand|
|income_consumption|input-data/income-consumption.csv|This is data put together by the USDA in their report U.S. Food Commodity Consumption Broken Down by Demographics, 1994-2008. The data was converted from pdf charts to a csv file. This is a subset of this data on consumption by income bracket. 185-percent of Federal Poverty Line is the cutoff between low and high income.|[https://www.ers.usda.gov/publications/pub-details/?pubid=45530](https://www.ers.usda.gov/publications/pub-details/?pubid=45530)||
|lafa_calories|input-data/food-availability-2007-2017.csv|This was derived from a USDA data set of Loss-Adjusted Food Availability in calories. Each of the food types that were tracked in the income_consumption data were extracted from this data and grouped into the food type. For instance Apple juice, Apples, and Apples dried, were all combined by calories consumed. This data set was used to provide a ratio that adjusted consumption data from 2007 to 2017.|[https://www.ers.usda.gov/data-products/food-availability-per-capita-data-system/food-availability-per-capita-data-system/#Loss-Adjusted%20Food%20Availability](https://www.ers.usda.gov/data-products/food-availability-per-capita-data-system/food-availability-per-capita-data-system/#Loss-Adjusted%20Food%20Availability)|
|food_exports|input-data/food-exports-2017.csv|Food export and import data was retrieved from the International Trade Data API run by the US Census Bureau. More on this API can be found here [Guide_to_International_Trade_Datasets.pdf](https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf)|[https://api.census.gov/data/timeseries/intltrade/exports/porths?get=PORT,CTY_CODE,E_COMMODITY,E_COMMODITY_SDESC,AIR_VAL_MO,AIR_WGT_MO,CNT_WGT_MO,CNT_VAL_MO&YEAR=2017&SUMMARY_LVL=DET&COMM_LVL=HS6&E_COMMODITY=](https://api.census.gov/data/timeseries/intltrade/exports/porths?get=PORT,CTY_CODE,E_COMMODITY,E_COMMODITY_SDESC,AIR_VAL_MO,AIR_WGT_MO,CNT_WGT_MO,CNT_VAL_MO&YEAR=2017&SUMMARY_LVL=DET&COMM_LVL=HS6&E_COMMODITY=)|
|food_imports|input-data/food-imports-2017.csv|Food export and import data was retrieved from the International Trade Data API run by the US Census Bureau. More on this API can be found here [Guide_to_International_Trade_Datasets.pdf](https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf)|[https://api.census.gov/data/timeseries/intltrade/imports/porths?get=PORT,CTY_CODE,I_COMMODITY,I_COMMODITY_SDESC,GEN_VAL_MO,AIR_VAL_MO,AIR_WGT_MO,CNT_WGT_MO,CNT_VAL_MO&YEAR=2017&SUMMARY_LVL=DET&COMM_LVL=HS6&I_COMMODITY='](https://api.census.gov/data/timeseries/intltrade/imports/porths?get=PORT,CTY_CODE,I_COMMODITY,I_COMMODITY_SDESC,GEN_VAL_MO,AIR_VAL_MO,AIR_WGT_MO,CNT_WGT_MO,CNT_VAL_MO&YEAR=2017&SUMMARY_LVL=DET&COMM_LVL=HS6&I_COMMODITY=')|
|imports_crosswalk|input-data/import-commodities.csv|This data crosswalks all import commodity names with our crop names used in the tool. The Calorie values for the import food types were derived from the USDA tool, Food Data Central [https://fdc.nal.usda.gov/index.html](https://fdc.nal.usda.gov/index.html)|[https://fdc.nal.usda.gov/index.html](https://fdc.nal.usda.gov/index.html)|
|population_income|input-data/input-data/ACSST5Y2021.S1701-Data.csv|Population data was retrieved from the census bureau. POVERTY STATUS IN THE PAST 12 MONTHS ACS 5-Year Estimates Subject Tables for 2021 was the report that was used. In our consumption data, below 185% of poverty line is low income. Above 185% is high income.|[https://data.census.gov/table?q=POVERTY+STATUS+IN+THE+PAST+12+MONTHS&g=010XX00US$0500000&tid=ACSST5Y2021.S1701](https://data.census.gov/table?q=POVERTY+STATUS+IN+THE+PAST+12+MONTHS&g=010XX00US$0500000&tid=ACSST5Y2021.S1701)|
|county_boundaries|input-data/geo-boundaries-2022/cb_2022_us_county_500k.shp|Geographic boundaries of counties in 2022. Population data was joined to these boundaries.|[https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html#:~:text=1%20%3A%20500%2C000%20(national)%C2%A0%20shapefile%20%5B11%20MB%5D%C2%A0%20%7C%C2%A0%20kml%20%5B8.2%20MB%5D)|
|port_codes|input-data/port-codes.csv|This is a table charting 4-digit port codes to the cities where they are located.|[https://www.census.gov/foreign-trade/schedules/d/dist.txt](https://www.census.gov/foreign-trade/schedules/d/dist.txt)|
