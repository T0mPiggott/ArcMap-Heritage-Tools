# --- ZTV Tool ------------------------------------------------------------------------------

import arcpy, glob, os, shutil, datetime
from arcpy.sa import *

# --- Tool input parameters ------------------------------------------------------------------------------
# siteBoundaryType = Site boundary type - Boundary/Coordinates (Value List String)
inLocation = arcpy.GetParameterAsText(0)
#GIS folder for the ZTV working data - Required data (folder location)
GISFolder = arcpy.GetParameterAsText(1)
#Geodatabas location - should be the project data folder
geodatabase = arcpy.GetParameterAsText(2)
# viewRadius = Radius of the viewshed (String; optional)
viewRadius = arcpy.GetParameterAsText(3)
# offsetA = Height of point when considered for visibility (metres) - (String; optional)
offsetA = arcpy.GetParameterAsText(4)
# --------------------------------------------------------------------------------------------------------

# --- Check out Spatial Analyst --------------------------------------------------------------------------
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
# --------------------------------------------------------------------------------------------------------
try:
    # Set up folder paths
    ztvFolder = os.path.join(GISFolder, "ZTV")
    arcpy.CreateFolder_management(GISFolder, "ZTV")
    # --------------------------------------------------------------------
    
    # Define British National Grid for new datasets ----------------------
    bng = "PROJCS['British_National_Grid',GEOGCS['GCS_OSGB_1936',DATUM['D_OSGB_1936',SPHEROID['Airy_1830',6377563.396,299.3249646]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',400000.0],PARAMETER['False_Northing',-100000.0],PARAMETER['Central_Meridian',-2.0],PARAMETER['Scale_Factor',0.9996012717],PARAMETER['Latitude_Of_Origin',49.0],UNIT['Meter',1.0]]"

    # Check inLocation geometry type - is it a point, line or polygon? ---
    inLocationGeometryDesc = arcpy.Describe(inLocation)
    inLocationGeometry = inLocationGeometryDesc.shapeType

    #create the feature dataset in the geodatabase to store the data
    out_dataset_path = geodatabase
    out_name = "ztv"


    # Execute CreateFeaturedataset
    arcpy.CreateFeatureDataset_management(out_dataset_path, out_name, )

    #---------------------------------------------------------------------------------------
    searchArea = os.path.join(ztvFolder, "StudyArea.shp")
    # Buffer...
    arcpy.Buffer_analysis(inLocation, searchArea, "1000 Meters", "", "", "ALL")
    arcpy.MakeFeatureLayer_management(searchArea, "searchArea_lyr")
    # --------------------------------------------------------------------------------------
    # locate the polygon to check what country the site is in
    gbPoly = "K:/GIS/Data/OpenData/OS_OpenData/Boundary-Line/data/great_britain.shp"
    arcpy.MakeFeatureLayer_management (gbPoly, "gbPoly_lyr")

    # Variables used to show whether ZTV study area falls in England, Wales or Scotland
    inScotland = 0
    inEngland = 0
    inWales = 0
    arcpy.SelectLayerByLocation_management("gbPoly_lyr", "INTERSECT", "searchArea_lyr")

    with arcpy.da.SearchCursor("gbPoly_lyr", ("NAME",)) as cursor:
        for row in cursor:
            if row[0] == "Scotland":
                inScotland = 1
            elif row[0] == "England":
                inEngland = 1
            elif row[0] == "Wales":
                inWales = 1

    arcpy.SelectLayerByAttribute_management("gbPoly_lyr", "CLEAR_SELECTION")

    # Variables used to show whether ZTV study area falls in England, Wales or Scotland
    inScotlandZTV = 0
    inEnglandZTV = 0
    inWalesZTV = 0

    arcpy.SelectLayerByLocation_management("gbPoly_lyr", "INTERSECT", inLocation, int(viewRadius))
    with arcpy.da.SearchCursor("gbPoly_lyr", ("NAME",)) as cursorZTV:
        for rowZTV in cursorZTV:
            if rowZTV[0] == "Scotland":
                inScotlandZTV = 1
            elif rowZTV[0] == "England":
                inEnglandZTV = 1
            elif rowZTV[0] == "Wales":
                inWalesZTV = 1
    # ---------------------------------------------------------------------------------------------
    #------------------------------------------------------#

    #set the paths to the datasets to be used to extract in the ZTV. Only those in the defined country will be set up
    if inEngland == 1:
        # Set up paths --------------------------------------------------------------
        bfPath = "K:\GIS\Data\HistoricEngland\Battlefields\Battlefields.shp"
        lbPtPath = "K:\GIS\Data\HistoricEngland\Listed Buildings\ListedBuildings.shp"
        pgPath = "K:\GIS\Data\HistoricEngland\Parks and Gardens\ParksAndGardens.shp"
        smPath = "K:\GIS\Data\HistoricEngland\Scheduled Monuments\ScheduledMonuments.shp"
        whPath = "K:\GIS\Data\HistoricEngland\World Heritage Sites\WorldHeritageSites.shp"
        # ---------------------------------------------------------------------------------------------------
        # Make feature layers for spatial selecting ---------------------------------------------------------
        arcpy.MakeFeatureLayer_management(bfPath, "Battlefields_lyr_HE")
        arcpy.MakeFeatureLayer_management(lbPtPath, "ListedBuildings_lyr_HE")
        arcpy.MakeFeatureLayer_management(pgPath, "ParksGardens_lyr_HE")
        arcpy.MakeFeatureLayer_management(smPath, "ScheduledMonuments_lyr_HE")
        arcpy.MakeFeatureLayer_management(whPath, "WorldHeritageSites_lyr_HE")
        # ---------------------------------------------------------------------------------------------------
    if inScotland == 1:
        # Set up paths --------------------------------------------------------------------------------------
        bfPath = "K:\GIS\Data\HistoricScotland\BattlefieldsInventory\Battlefields_inventory_boundary.shp"
        caPath = "K:\GIS\Data\HistoricScotland\ConservationAreas\Conservation_Areas.shp"
        lbPtPath = "K:\GIS\Data\HistoricScotland\ListedBuildings\Listed_Buildings.shp"
        gdlPath = "K:\GIS\Data\HistoricScotland\GardensAndDesignedLandscapes\Gardens_and_Designed_Landscapes.shp"
        smPath = "K:\GIS\Data\HistoricScotland\ScheduledMonuments\Scheduled_Monuments.shp"
        whPath = "K:\GIS\Data\HistoricScotland\WorldHeritageSites\World_Heritage_Sites.shp"
        # ---------------------------------------------------------------------------------------------------
        # Make feature layers for spatial selecting ---------------------------------------------------------
        arcpy.MakeFeatureLayer_management(bfPath, "Battlefields_lyr_HS")
        arcpy.MakeFeatureLayer_management(caPath, "ConservationAreas_lyr_HS")
        arcpy.MakeFeatureLayer_management(lbPtPath, "ListedBuildings_lyr_HS")
        arcpy.MakeFeatureLayer_management(gdlPath, "gardensDesignedLandscapes_lyr_HS")
        arcpy.MakeFeatureLayer_management(smPath, "ScheduledMonuments_lyr_HS")
        arcpy.MakeFeatureLayer_management(whPath, "WorldHeritageSites_lyr_HS")
         # ---------------------------------------------------------------------------------------------------
    if inWales == 1:
        # Set up paths
        caPath = "K:/GIS/Data/Cadw/ConservationAreas.shp"
        hlaPath = "K:/GIS/Data/Cadw/HistoricLandscapesAreas.shp"
        lbPtPath = "K:/GIS/Data/Cadw/ListedBuildings.shp"
        pgPath = "K:/GIS/Data/Cadw/Parks.shp"
        smPath = "K:/GIS/Data/Cadw/ScheduledMonuments.shp"
        whPath = "K:/GIS/Data/Cadw/WorldHeritageSites.shp"
        landmapCLPath = "K:/GIS/Data/NRW/Landmap/CulturalLandscape/Cultural_Landscape/ESRI_Cultural_Landscape_All_Wales.shp"
        landmapHLPath = "K:/GIS/Data/NRW/Landmap/HistoricLandscape/Historic_Landscape/ESRI_Historic_Landscape_All_Wales.shp"
        landmapVSPath = "K:/GIS/Data/NRW/Landmap/VisualSensory/Visual_Sensory/ESRI_Visual_Sensory_All_Wales.shp"

        # Make feature layers for spatial selections ---------------------------------------------------------------------------------
        arcpy.MakeFeatureLayer_management(caPath, "ConservationAreas_lyr_Cadw")
        arcpy.MakeFeatureLayer_management(hlaPath, "HistoricLandscapeAreas_lyr_Cadw")
        arcpy.MakeFeatureLayer_management(lbPtPath, "ListedBuildings_lyr_Cadw")
        arcpy.MakeFeatureLayer_management(pgPath, "ParksGardens_lyr_Cadw")
        arcpy.MakeFeatureLayer_management(smPath, "ScheduledMonuments_lyr_Cadw")
        arcpy.MakeFeatureLayer_management(whPath, "WorldHeritageSites_lyr_Cadw")

        arcpy.MakeFeatureLayer_management(landmapCLPath, "CulturalLandscape_lyr")
        arcpy.MakeFeatureLayer_management(landmapHLPath, "HistoricLandscape_lyr")
        arcpy.MakeFeatureLayer_management(landmapVSPath, "VisualSensory_lyr")
    # ------------------------------------------------------------------------------
    # --- Extract designations ---------------------------------------------------------------------------------------------------------------------
    arcpy.AddMessage("Extracting designations data for the study area")
    # --- Set up all designated data paths for the created featureclasses -------------------------------------------------------
    # --- English designations ---------------------------------------------------------------------------------------------
    eh_battlefieldPolygonPathZTV = os.path.join(geodatabase, "ztv", "ZTV_HE_Battlefields")
    eh_listedBuildingPointPathZTV = os.path.join(geodatabase, "ztv", "ZTV_HE_ListedBuildings")
    eh_parksGardensPolygonPathZTV = os.path.join(geodatabase, "ztv", "ZTV_HE_ParksGardens")
    eh_scheduledMonumentsPolygonPathZTV = os.path.join(geodatabase, "ztv", "ZTV_HE_ScheduledMonuments")
    eh_worldHeritageSitesPolygonPathZTV = os.path.join(geodatabase, "ztv", "ZTV_HE_WorldHeritageSites")
    # ----------------------------------------------------------------------------------------------------------------------
    # --- Output paths for Welsh data --------------------------------------------------------------------------------------
    cadw_conservationAreasZTV = os.path.join(geodatabase, "ztv", "ZTV_Cadw_ConservationAreas")
    cadw_historicLandscapeAreasZTV = os.path.join(geodatabase, "ztv", "ZTV_Cadw_HistoricLandscapeAreas")
    cadw_listedBuildingPointPathZTV = os.path.join(geodatabase, "ztv","ZTV_Cadw_ListedBuildings")
    cadw_parksGardensPolygonPathZTV = os.path.join(geodatabase,"ztv",  "ZTV_Cadw_ParksGardens")
    cadw_scheduledMonumentsPolygonPathZTV = os.path.join(geodatabase,"ztv", "ZTV_Cadw_ScheduledMonuments")
    cadw_worldHeritageSitesPolygonPathZTV = os.path.join(geodatabase,"ztv", "ZTV_Cadw_WorldHeritageSites")
    # Landmap data
    landmapCulturalPathZTV = os.path.join(geodatabase,"ztv",  "ZTV_CCW_Landmap_CulturalLandscape")
    landmapHistoricPathZTV = os.path.join(geodatabase,"ztv",  "ZTV_CCW_Landmap_HistoricLandscape")
    landmapVisSensPathZTV = os.path.join(geodatabase,"ztv",  "ZTV_CCW_Landmap_VIsualSensory")
    # ----------------------------------------------------------------------------------------------------------------------
    # --- Scottish designations data ---------------------------------------------------------------------------------------
    hs_battlefieldsZTV = os.path.join(geodatabase,"ztv", "ZTV_HS_Battlefields")
    hs_conservationAreasZTV = os.path.join(geodatabase,"ztv",  "ZTV_HS_ConservationAreas")
    hs_listedBuildingPointPathZTV = os.path.join(geodatabase,"ztv", "ZTV_HS_ListedBuildings")
    hs_gardensDesignedLandscapesZTV = os.path.join(geodatabase,"ztv",  "ZTV_HS_GardensDesignedLandscapes")
    hs_scheduledMonumentsPolygonPathZTV = os.path.join(geodatabase,"ztv", "ZTV_HS_ScheduledMonuments")
    hs_worldHeritageSitesPolygonPathZTV = os.path.join(geodatabase,"ztv", "ZTV_HS_WorldHeritageSites")
    # ----------------------------------------------------------------------------------------------------------------------

    # --- Set the location of the T50 data (for viewsheds) ---------------------------------------------------
    terrain50 = "k:/GIS/Data/OpenData/OS_OpenData/Terrain50/Terrain50.gdb/Terrain50"
    # ----------------------------------------------------------------------------------------------------------------------

    # --- Create ZTV target points ---------------------------------------------------------------------------
    arcpy.SetProgressorLabel("Creating the viewshed")
    arcpy.AddMessage("Creating the viewshed")
    # --------------------------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------------------------

    # --- Create a target point grid covering the site boundary ----------------------------------------------
    if inLocationGeometry == "Point":
        inObserver = inLocation
    elif inLocationGeometry == "Polyline":
        inObserver = inLocation
    else:
        # Create target points -------------------------------------------------------------------------------
        # Paths of temporary files
        outputFishnetClass = os.path.join(ztvFolder, "tmpGrid.shp")
        outputFishnetClassPts = os.path.join(ztvFolder, "tmpGrid_label.shp")
        outputEnvelope = os.path.join(ztvFolder, "outputEnvelope.shp")

        # Step 1 - Envelope site
        arcpy.MinimumBoundingGeometry_management(inLocation, outputEnvelope, "ENVELOPE", "ALL")

        # Step 2 - Get the coordinates for the envelope
        minX = inLocationGeometryDesc.extent.XMin
        maxX = inLocationGeometryDesc.extent.XMax
        minY = inLocationGeometryDesc.extent.YMin
        maxY = inLocationGeometryDesc.extent.YMax
        # Create boundary points from envelope
        bottomCorner = arcpy.Point(minX, minY)
        topCorner = arcpy.Point(maxX, maxY)
        # Set the origin of the fishnet
        originCoord = "%f %f" % (bottomCorner.X, bottomCorner.Y)
        # Set the orientation
        yAxisCoord = "%f %f" % (bottomCorner.X, (bottomCorner.Y + 1))
        # Set the opposite corner
        oppositeCorner = "%f %f" % (topCorner.X, topCorner.Y)

        # Step 3 - Create the grid
        arcpy.CreateFishnet_management(outputFishnetClass, originCoord, yAxisCoord, "50", "50", "0", "0",
                                       oppositeCorner, "LABELS")
        # Make feature layers for selection
        arcpy.MakeFeatureLayer_management(inLocation, "Site_lyr")
        fileTest = os.path.isfile(outputFishnetClassPts)
        arcpy.MakeFeatureLayer_management(outputFishnetClassPts, "TargetPoints_lyr")

        # Step 4 - Select those points outside inLocation
        arcpy.SelectLayerByLocation_management("TargetPoints_lyr", "INTERSECT", "Site_lyr")

        # Step 5 - Export final target points
        inObserver = os.path.join(ztvFolder, "TargetPoints.shp")

        # Step 6 - Count the points to ensure that target points exist
        targetCount = arcpy.GetCount_management("TargetPoints_lyr")

        if str(targetCount) == "0":
            # If no points are selected out then create the centroid
            arcpy.FeatureToPoint_management(inLocation, inObserver, "INSIDE")
        else:
            # If there are points then save
            arcpy.CopyFeatures_management("TargetPoints_lyr", inObserver)
        # ----------------------------------------------------------------------------------------------------

    # Create the ZTV ------------------------------------------------------------------------------------
    # Path to save raster to...
    finalRaster = os.path.join(ztvFolder, "Viewshed")
    arcpy.SetProgressorLabel("Extracting elevation data")
    # First buffer the point(s) to get the clip area...
    outBuffer = os.path.join(ztvFolder, "ViewshedStudyArea.shp")
    arcpy.Buffer_analysis(inObserver, outBuffer, viewRadius)
    # Create a dissolved version of the buffer
    arcpy.SetProgressorLabel("Creating the ZTV 'study area'")
    outDissolvedBuffer = os.path.join(geodatabase, "ztv", "ZTV_StudyArea")
    arcpy.Dissolve_management(outBuffer, outDissolvedBuffer)
    arcpy.MakeFeatureLayer_management(outDissolvedBuffer, "viewshedStudyArea_lyr")
    # Clip Terrain50
    inRaster = os.path.join(ztvFolder, "Elevation")
    arcpy.Clip_management(terrain50, "#", inRaster, outBuffer)
    # Add attributes to input to calculate
    arcpy.SetProgressorLabel("Setting up the observers layer for analysis")
    arcpy.AddField_management(inObserver,"OFFSETA","DOUBLE","","","","","NON_NULLABLE","REQUIRED")
    if offsetA != "":
        arcpy.CalculateField_management(inObserver, "OFFSETA", offsetA, "PYTHON")
    else:
        arcpy.CalculateField_management(inObserver, "OFFSETB", "1.7", "PYTHON")
    if viewRadius == "":
        viewRadius = "5000"
        arcpy.AddField_management(inObserver,"OFFSETB","DOUBLE","","","","","NON_NULLABLE","REQUIRED")
        arcpy.CalculateField_management(inObserver, "OFFSETB", "1.6", "PYTHON")
        arcpy.AddField_management(inObserver,"RADIUS2","DOUBLE","","","","","NON_NULLABLE","REQUIRED")
        arcpy.CalculateField_management(inObserver, "RADIUS2", viewRadius, "PYTHON")
        arcpy.AddMessage("Running the analysis...")
        arcpy.SetProgressorLabel("Running the analysis...")
    # Create the viewshed
    outViewshed = Viewshed(inRaster, inObserver)
    # Save the viewshed
    outViewshed.save(finalRaster)
    # Convert viewshed to poly
    arcpy.SetProgressorLabel("Converting the viewshed to a polygon shapefile")
    # Temporary file
    convertedViewshedOut = os.path.join(ztvFolder, "viewshed_polygon.shp")
    arcpy.RasterToPolygon_conversion(outViewshed, convertedViewshedOut, "NO_SIMPLIFY")
    # Select the area with visibility from the converted viewshed
    arcpy.MakeFeatureLayer_management(convertedViewshedOut, "viewshed_lyr")
    arcpy.SelectLayerByAttribute_management ("viewshed_lyr", "NEW_SELECTION", "GRIDCODE > 0")
    # Save layer
    outViewshedVector = os.path.join(geodatabase,"ztv", "ZTV_VisibleArea")
    arcpy.CopyFeatures_management("viewshed_lyr", outViewshedVector)

    # --- Spatially select designations data within the visible area ---------------------------------------------
    # --- Select countries within the ZTV area -------------------------------------------------------------------
    # --- If in England... ---------------------------------------------------------------------------------------
    if inEngland == 1:
            arcpy.SetProgressorLabel("Extracting visible designations within England")

            # Battlefields
            arcpy.SetProgressorLabel("Extracting visible Battlefields data")
            arcpy.SelectLayerByLocation_management("Battlefields_lyr_HE", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("Battlefields_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Battlefields within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("Battlefields_lyr_HE", eh_battlefieldPolygonPathZTV)
                arcpy.MakeFeatureLayer_management(eh_battlefieldPolygonPathZTV, "Battlefields_lyr_HE_ZTV")
                arcpy.AddField_management("Battlefields_lyr_HE_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("Battlefields_lyr_HE_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("Battlefields_lyr_HE_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("Battlefields_lyr_HE_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

                # Listed Buildings
            arcpy.SetProgressorLabel("Extracting visible Listed Buildings data")
            arcpy.SelectLayerByLocation_management("ListedBuildings_lyr_HE", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("ListedBuildings_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Listed Buildings within the ZTV study area")
            else:
                featuresCount = arcpy.GetCount_management("ListedBuildings_lyr_HE")
                if str(featuresCount) == "0":
                    arcpy.AddMessage("No Listed Buildings within the ZTV study area")
                else:
                    arcpy.CopyFeatures_management("ListedBuildings_lyr_HE", eh_listedBuildingPointPathZTV)
                    arcpy.MakeFeatureLayer_management(eh_listedBuildingPointPathZTV, "ListedBuildings_lyr_HE_ZTV")
                    arcpy.AddField_management("ListedBuildings_lyr_HE_ZTV", "Visible", "TEXT", "", "", 20)
                    arcpy.CalculateField_management("ListedBuildings_lyr_HE_ZTV", "Visible", "'No'", "PYTHON_9.3")
                    arcpy.SelectLayerByLocation_management("ListedBuildings_lyr_HE_ZTV", "INTERSECT", "viewshed_lyr")
                    arcpy.CalculateField_management("ListedBuildings_lyr_HE_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # Parks and Gardens
            arcpy.SetProgressorLabel("Extracting visible Parks and Gardens data")
            arcpy.SelectLayerByLocation_management("ParksGardens_lyr_HE", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("ParksGardens_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Parks and Gardens within the ZTV study area")
            else:
                featuresCount = arcpy.GetCount_management("ParksGardens_lyr_HE")
                if str(featuresCount) == "0":
                    arcpy.AddMessage("No Parks and Gardens within the ZTV study area")
                else:
                    arcpy.CopyFeatures_management("ParksGardens_lyr_HE", eh_parksGardensPolygonPathZTV)
                    arcpy.MakeFeatureLayer_management(eh_parksGardensPolygonPathZTV, "ParksGardens_lyr_HE_ZTV")
                    arcpy.AddField_management("ParksGardens_lyr_HE_ZTV", "Visible", "TEXT", "", "", 20)
                    arcpy.CalculateField_management("ParksGardens_lyr_HE_ZTV", "Visible", "'No'", "PYTHON_9.3")
                    arcpy.SelectLayerByLocation_management("ParksGardens_lyr_HE_ZTV", "INTERSECT", "viewshed_lyr")
                    arcpy.CalculateField_management("ParksGardens_lyr_HE_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # Scheduled Monuments
            arcpy.SetProgressorLabel("Extracting visible Scheduled Monuments data")
            arcpy.SelectLayerByLocation_management("ScheduledMonuments_lyr_HE", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("ScheduledMonuments_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Scheduled Monuments within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("ScheduledMonuments_lyr_HE", eh_scheduledMonumentsPolygonPathZTV)
                arcpy.MakeFeatureLayer_management(eh_scheduledMonumentsPolygonPathZTV, "ScheduledMonuments_lyr_HE_ZTV")
                arcpy.AddField_management("ScheduledMonuments_lyr_HE_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("ScheduledMonuments_lyr_HE_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("ScheduledMonuments_lyr_HE_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("ScheduledMonuments_lyr_HE_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # World Heritage Sites
            arcpy.SetProgressorLabel("Extracting visible World Heritage Sites data")
            arcpy.SelectLayerByLocation_management("WorldHeritageSites_lyr_HE", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("WorldHeritageSites_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No World Heritage Sites within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("WorldHeritageSites_lyr_HE", eh_worldHeritageSitesPolygonPathZTV)
                arcpy.MakeFeatureLayer_management(eh_worldHeritageSitesPolygonPathZTV, "WorldHeritageSites_lyr_HE_ZTV")
                arcpy.AddField_management("WorldHeritageSites_lyr_HE_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("WorldHeritageSites_lyr_HE_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("WorldHeritageSites_lyr_HE_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("WorldHeritageSites_lyr_HE_ZTV", "Visible", "'Yes'", "PYTHON_9.3")
        # ------------------------------------------------------------------------------------------------------------
        # --- If in Wales... -----------------------------------------------------------------------------------------
    if inWales == 1:
            arcpy.SetProgressorLabel("Extracting visible designations within Wales")

            # Historic landscape areas
            arcpy.SetProgressorLabel("Extracting visible Historic Landscape Areas data")
            arcpy.SelectLayerByLocation_management("HistoricLandscapeAreas_lyr_Cadw", "INTERSECT",
                                                   "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("HistoricLandscapeAreas_lyr_Cadw")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Historic Landscape Areas within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("HistoricLandscapeAreas_lyr_Cadw", cadw_historicLandscapeAreasZTV)
                arcpy.MakeFeatureLayer_management(cadw_historicLandscapeAreasZTV, "HistoricLandscapeAreas_lyr_Cadw_ZTV")
                arcpy.AddField_management("HistoricLandscapeAreas_lyr_Cadw_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("HistoricLandscapeAreas_lyr_Cadw_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("HistoricLandscapeAreas_lyr_Cadw_ZTV", "INTERSECT",
                                                       "viewshed_lyr")
                arcpy.CalculateField_management("HistoricLandscapeAreas_lyr_Cadw_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # Conservation areas
            arcpy.SetProgressorLabel("Extracting visible Conservation Areas data")
            arcpy.SelectLayerByLocation_management("ConservationAreas_lyr_Cadw", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("ConservationAreas_lyr_Cadw")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Conservation Areas within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("ConservationAreas_lyr_Cadw", cadw_conservationAreasZTV)
                arcpy.MakeFeatureLayer_management(cadw_conservationAreasZTV, "ConservationAreas_lyr_Cadw_ZTV")
                arcpy.AddField_management("ConservationAreas_lyr_Cadw_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("ConservationAreas_lyr_Cadw_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("ConservationAreas_lyr_Cadw_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("ConservationAreas_lyr_Cadw_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # Listed Buildings
            arcpy.SetProgressorLabel("Extracting visible Listed Buildings data")
            arcpy.SelectLayerByLocation_management("ListedBuildings_lyr_Cadw", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("ListedBuildings_lyr_Cadw")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Listed Buildings within the ZTV study area")
            else:
                featuresCount = arcpy.GetCount_management("ListedBuildings_lyr_Cadw")
                if str(featuresCount) == "0":
                    arcpy.AddMessage("No Listed Buildings within the ZTV study area")
                else:
                    arcpy.CopyFeatures_management("ListedBuildings_lyr_Cadw", cadw_listedBuildingPointPathZTV)
                    arcpy.MakeFeatureLayer_management(cadw_listedBuildingPointPathZTV, "ListedBuildings_lyr_Cadw_ZTV")
                    arcpy.AddField_management("ListedBuildings_lyr_Cadw_ZTV", "Visible", "TEXT", "", "", 20)
                    arcpy.CalculateField_management("ListedBuildings_lyr_Cadw_ZTV", "Visible", "'No'", "PYTHON_9.3")
                    arcpy.SelectLayerByLocation_management("ListedBuildings_lyr_Cadw_ZTV", "INTERSECT", "viewshed_lyr")
                    arcpy.CalculateField_management("ListedBuildings_lyr_Cadw_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # Parks and Gardens
            arcpy.SetProgressorLabel("Extracting visible Parks and Gardens data")
            arcpy.SelectLayerByLocation_management("ParksGardens_lyr_Cadw", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("ParksGardens_lyr_Cadw")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Parks and Gardens within the ZTV study area")
            else:
                featuresCount = arcpy.GetCount_management("ParksGardens_lyr_Cadw")
                if str(featuresCount) == "0":
                    arcpy.AddMessage("No Parks and Gardens within the ZTV study area")
                else:
                    arcpy.CopyFeatures_management("ParksGardens_lyr_Cadw", cadw_parksGardensPolygonPathZTV)
                    arcpy.MakeFeatureLayer_management(cadw_parksGardensPolygonPathZTV, "ParksGardens_lyr_Cadw_ZTV")
                    arcpy.AddField_management("ParksGardens_lyr_Cadw_ZTV", "Visible", "TEXT", "", "", 20)
                    arcpy.CalculateField_management("ParksGardens_lyr_Cadw_ZTV", "Visible", "'No'", "PYTHON_9.3")
                    arcpy.SelectLayerByLocation_management("ParksGardens_lyr_Cadw_ZTV", "INTERSECT", "viewshed_lyr")
                    arcpy.CalculateField_management("ParksGardens_lyr_Cadw_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # Scheduled Monuments
            arcpy.SetProgressorLabel("Extracting visible Scheduled Monuments data")
            arcpy.SelectLayerByLocation_management("ScheduledMonuments_lyr_Cadw", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("ScheduledMonuments_lyr_Cadw")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Scheduled Monuments within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("ScheduledMonuments_lyr_Cadw", cadw_scheduledMonumentsPolygonPathZTV)
                arcpy.MakeFeatureLayer_management(cadw_scheduledMonumentsPolygonPathZTV,
                                                  "ScheduledMonuments_lyr_Cadw_ZTV")
                arcpy.AddField_management("ScheduledMonuments_lyr_Cadw_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("ScheduledMonuments_lyr_Cadw_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("ScheduledMonuments_lyr_Cadw_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("ScheduledMonuments_lyr_Cadw_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # World Heritage Sites
            arcpy.SetProgressorLabel("Extracting visible World Heritage Sites data")
            arcpy.SelectLayerByLocation_management("WorldHeritageSites_lyr_Cadw", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("WorldHeritageSites_lyr_Cadw")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No World Heritage Sites within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("WorldHeritageSites_lyr_Cadw", cadw_worldHeritageSitesPolygonPathZTV)
                arcpy.MakeFeatureLayer_management(cadw_worldHeritageSitesPolygonPathZTV,
                                                  "WorldHeritageSites_lyr_Cadw_ZTV")
                arcpy.AddField_management("WorldHeritageSites_lyr_Cadw_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("WorldHeritageSites_lyr_Cadw_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("WorldHeritageSites_lyr_Cadw_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("WorldHeritageSites_lyr_Cadw_ZTV", "Visible", "'Yes'", "PYTHON_9.3")
        # ------------------------------------------------------------------------------------------------------------
        # --- If in Scotland... --------------------------------------------------------------------------------------
    if inScotland == 1:
            arcpy.SetProgressorLabel("Extracting visible designations within Scotland")

            # Battlefields
            arcpy.SetProgressorLabel("Extracting visible battlefields data")
            arcpy.SelectLayerByLocation_management("Battlefields_lyr_HS", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("Battlefields_lyr_HS")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No battlefields within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("Battlefields_lyr_HS", hs_battlefieldsZTV)
                arcpy.MakeFeatureLayer_management(hs_battlefieldsZTV, "Battlefields_lyr_HS_ZTV")
                arcpy.AddField_management("Battlefields_lyr_HS_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("Battlefields_lyr_HS_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("Battlefields_lyr_HS_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("Battlefields_lyr_HS_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # Conservation areas
            arcpy.SetProgressorLabel("Extracting visible Conservation Areas data")
            arcpy.SelectLayerByLocation_management("ConservationAreas_lyr_HS", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("ConservationAreas_lyr_HS")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Conservation Areas within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("ConservationAreas_lyr_HS", hs_conservationAreasZTV)
                arcpy.MakeFeatureLayer_management(hs_conservationAreasZTV, "ConservationAreas_lyr_HS_ZTV")
                arcpy.AddField_management("ConservationAreas_lyr_HS_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("ConservationAreas_lyr_HS_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("ConservationAreas_lyr_HS_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("ConservationAreas_lyr_HS_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # Listed Buildings
            arcpy.SetProgressorLabel("Extracting visible listed buildings data")
            arcpy.SelectLayerByLocation_management("ListedBuildings_lyr_HS", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("ListedBuildings_lyr_HS")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Listed Buildings within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("ListedBuildings_lyr_HS", hs_listedBuildingPointPathZTV)
                arcpy.MakeFeatureLayer_management(hs_listedBuildingPointPathZTV, "ListedBuildings_lyr_HS_ZTV")
                arcpy.AddField_management("ListedBuildings_lyr_HS_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("ListedBuildings_lyr_HS_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("ListedBuildings_lyr_HS_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("ListedBuildings_lyr_HS_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # Parks and Gardens
            arcpy.SetProgressorLabel("Extracting visible gardens and designed landscapes data")
            arcpy.SelectLayerByLocation_management("gardensDesignedLandscapes_lyr_HS", "INTERSECT",
                                                   "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("gardensDesignedLandscapes_lyr_HS")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Gardens and Designed Landscapes within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("gardensDesignedLandscapes_lyr_HS", hs_gardensDesignedLandscapesZTV)
                arcpy.MakeFeatureLayer_management(hs_gardensDesignedLandscapesZTV,
                                                  "gardensDesignedLandscapes_lyr_HS_ZTV")
                arcpy.AddField_management("gardensDesignedLandscapes_lyr_HS_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("gardensDesignedLandscapes_lyr_HS_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("gardensDesignedLandscapes_lyr_HS_ZTV", "INTERSECT",
                                                       "viewshed_lyr")
                arcpy.CalculateField_management("gardensDesignedLandscapes_lyr_HS_ZTV", "Visible", "'Yes'",
                                                "PYTHON_9.3")

            # Scheduled Monuments
            arcpy.SetProgressorLabel("Extracting visible Scheduled Monuments data")
            arcpy.SelectLayerByLocation_management("ScheduledMonuments_lyr_HS", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("ScheduledMonuments_lyr_HS")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No Scheduled Monuments within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("ScheduledMonuments_lyr_HS", hs_scheduledMonumentsPolygonPathZTV)
                arcpy.MakeFeatureLayer_management(hs_scheduledMonumentsPolygonPathZTV, "ScheduledMonuments_lyr_HS_ZTV")
                arcpy.AddField_management("ScheduledMonuments_lyr_HS_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("ScheduledMonuments_lyr_HS_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("ScheduledMonuments_lyr_HS_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("ScheduledMonuments_lyr_HS_ZTV", "Visible", "'Yes'", "PYTHON_9.3")

            # World Heritage Sites
            arcpy.SetProgressorLabel("Extracting visible World Heritage Sites data")
            arcpy.SelectLayerByLocation_management("WorldHeritageSites_lyr_HS", "INTERSECT", "viewshedStudyArea_lyr")
            featuresCount = arcpy.GetCount_management("WorldHeritageSites_lyr_HS")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No World Heritage Sites within the ZTV study area")
            else:
                arcpy.CopyFeatures_management("WorldHeritageSites_lyr_HS", hs_worldHeritageSitesPolygonPathZTV)
                arcpy.MakeFeatureLayer_management(hs_worldHeritageSitesPolygonPathZTV, "WorldHeritageSites_lyr_HS_ZTV")
                arcpy.AddField_management("WorldHeritageSites_lyr_HS_ZTV", "Visible", "TEXT", "", "", 20)
                arcpy.CalculateField_management("WorldHeritageSites_lyr_HS_ZTV", "Visible", "'No'", "PYTHON_9.3")
                arcpy.SelectLayerByLocation_management("WorldHeritageSites_lyr_HS_ZTV", "INTERSECT", "viewshed_lyr")
                arcpy.CalculateField_management("WorldHeritageSites_lyr_HS_ZTV", "Visible", "'Yes'", "PYTHON_9.3")
    #-------------------------------------------------------------#
    # Delete working folders
    arcpy.SetProgressorLabel("Clearing up...")
    arcpy.AddMessage("Clearing up...")
    
    arcpy.Delete_management(ztvFolder)
    
except Exception as e:
    arcpy.AddError(e)













