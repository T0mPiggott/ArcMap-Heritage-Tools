# --- Tender GIS Setup tool ------------------------------------------------------------------------------#

import arcpy, glob, os, shutil, datetime, arcpy.mapping
from arcpy.sa import *

# --- Tool input parameters ------------------------------------------------------------------------------#
siteBoundaryType = arcpy.GetParameterAsText(0)
# inLocation = Site plan or points (Feature layer) - optional
inLocation = arcpy.GetParameterAsText(1)
# eastingIn = Coordinate option easting (String) - optional
eastingIn = arcpy.GetParameterAsText(2)
# northingIn = Coordinate option northing (String) - optional
northingIn = arcpy.GetParameterAsText(3)
# studyAreaSize = Study area buffer size (metres) (String)
studyAreaSize = arcpy.GetParameterAsText(4)
# siteName = Site name (String)
siteName = arcpy.GetParameterAsText(5)
# projectNumber = Project number (String)
projectNumber = arcpy.GetParameterAsText(6)
# GISFolder = Location of GIS folder (Folder)
GISFolder = arcpy.GetParameterAsText(7)
# geodatabase = location
geodatabase = arcpy.GetParameterAsText(8)
# --------------------------------------------------------------------------------------------------------

# --- Check out Spatial Analyst --------------------------------------------------------------------------
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
# --------------------------------------------------------------------------------------------------------
try:
    # Create sub-folders in GIS folder
    # --------------------------------------------------------------------#
    # Set up folder paths
    shpFolder = os.path.join(GISFolder, "SHP")
    rasterFolder = os.path.join(GISFolder, "Raster")
    workingVector = os.path.join(shpFolder, "VectorWorking")
    workingRaster = os.path.join(rasterFolder, "RasterWorking")

    # set up paths to scratch folders
    workingVector = os.path.join(shpFolder, "VectorWorking")
    workingRaster = os.path.join(rasterFolder, "RasterWorking")
    # Create site folder
    arcpy.CreateFolder_management(shpFolder, "Site")

    # Create working folders
    arcpy.CreateFolder_management(shpFolder, "VectorWorking")
    arcpy.CreateFolder_management(rasterFolder, "RasterWorking")

    # --------------------------------------------------------------------#
    # Define British National Grid for new datasets ----------------------#
    bng = "PROJCS['British_National_Grid',GEOGCS['GCS_OSGB_1936',DATUM['D_OSGB_1936',SPHEROID['Airy_1830',6377563.396,299.3249646]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',400000.0],PARAMETER['False_Northing',-100000.0],PARAMETER['Central_Meridian',-2.0],PARAMETER['Scale_Factor',0.9996012717],PARAMETER['Latitude_Of_Origin',49.0],UNIT['Meter',1.0]]"
    # --------------------------------------------------------------------#
    # --------------------------------------------------------------------#
    # convert site boundary provided as inLocation to the file geodatabase #
    arcpy.conversion.FeatureClassToGeodatabase(inLocation, geodatabase)

    # Check input type - if a coordinate then create point ---------------
    if siteBoundaryType == "Coordinates":
        point = arcpy.Point()
        pointGeometryList = []
        # Location from input X and Y
        point.X = eastingIn
        point.Y = northingIn
        # Create a point from XY
        pointGeometry = arcpy.PointGeometry(point)
        pointGeometryList.append(pointGeometry)
        # Temporary point shapefile location
        tmpPointLocation = os.path.join(workingVector, "SitePoint")
        # Create temporary point shapefile
        arcpy.CopyFeatures_management(pointGeometryList, tmpPointLocation)
        # Set as BNG
        arcpy.DefineProjection_management(tmpPointLocation, bng)
        # Set as site location
        inLocation = tmpPointLocation
    # --------------------------------------------------------------------

    # Check inLocation geometry type - is it a point, line or polygon? ---
    inLocationGeometryDesc = arcpy.Describe(inLocation)
    inLocationGeometry = inLocationGeometryDesc.shapeType
    # --------------------------------------------------------------------
    # Create study area -----------------------------------------------------------------
    arcpy.AddMessage("Creating the study area")
    arcpy.SetProgressorLabel("Creating the study area")
    studyAreaPrefix = siteName + "_" + projectNumber + "_StudyArea"
    searchArea = os.path.join(geodatabase, "Site_and_StudyArea", siteName + "_" + projectNumber + "_StudyArea")
    # Buffer...
    arcpy.Buffer_analysis(inLocation, searchArea, studyAreaSize, "", "", "ALL")
    arcpy.MakeFeatureLayer_management(searchArea, "searchArea_lyr")
    # -----------------------------------------------------------------------------------

    # Previous projects data ------------------------------------------------------------
    mappingFolder = "K:/GIS/Data/WA Mapping/SHP"

    studyAreas = os.path.join(mappingFolder, "WA_Project_Study_Areas.shp")
    projectCentroids = os.path.join(mappingFolder, "WA_ProjectCentroids.shp")
    siteBoundaries = os.path.join(mappingFolder, "WA_Project_Site_Boundaries.shp")
    otherAreas = os.path.join(mappingFolder, "WA_Project_Other_Areas.shp")
    excavatedAreas = os.path.join(mappingFolder, "WA_Project_Excavated_Areas.shp")
    evalTrenches = os.path.join(mappingFolder, "WA_Project_Eval_Trenches_and_Test_Pits.shp")

    arcpy.MakeFeatureLayer_management(studyAreas, "studyAreas_lyr")
    arcpy.MakeFeatureLayer_management(projectCentroids, "projectCentroids_lyr")
    arcpy.MakeFeatureLayer_management(siteBoundaries, "siteBoundaries_lyr")
    arcpy.MakeFeatureLayer_management(otherAreas, "otherAreas_lyr")
    arcpy.MakeFeatureLayer_management(excavatedAreas, "excavatedAreas_lyr")
    arcpy.MakeFeatureLayer_management(evalTrenches, "evalTrenches_lyr")

    # Output locations
    outputStudyAreas = os.path.join(geodatabase, "Wessex_Project_Data", "WA_StudyAreas")
    outputProjectCentroids = os.path.join(geodatabase, "Wessex_Project_Data", "WA_ProjectCentroids")
    outputSiteBoundaries = os.path.join(geodatabase, "Wessex_Project_Data", "WA_SiteBoundaries")
    outputOtherAreas = os.path.join(geodatabase, "Wessex_Project_Data", "WA_OtherAreas")
    outputExcavatedAreas = os.path.join(geodatabase, "Wessex_Project_Data", "WA_ExcavatedAreas")
    outputEvalTrenches = os.path.join(geodatabase, "Wessex_Project_Data", "WA_EvalTrenches")

    # --------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------
    # Country check - is the study area in England, Wales or Scotland? ----------------------------
    # Also checks for countries within ZTV study area
    gbPoly = "K:/GIS/Data/OpenData/OS_OpenData/Boundary-Line/data/great_britain.shp"

    arcpy.MakeFeatureLayer_management(gbPoly, "gbPoly_lyr")

    # Variables used to show whether study area falls in England, Wales or Scotland
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
    # ---------------------------------------------------------------------------------------------

    # --- Extract designations ---------------------------------------------------------------------------------------------------------------------
    arcpy.AddMessage("Extracting designations data for the study area")
    # --- Set up all designated data paths - required at this stage for setting up MXD links -------------------------------------------------------
    # --- English designations ---------------------------------------------------------------------------------------------
    eh_battlefieldPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HE_Battlefields")
    eh_listedBuildingPointPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HE_ListedBuildings")
    eh_parksGardensPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HE_ParksGardens")
    eh_scheduledMonumentsPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HE_ScheduledMonuments")
    eh_worldHeritageSitesPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HE_WorldHeritageSites")
    eh_certificatesOfImmunityPointsPath = os.path.join(geodatabase, "Designated_Heritage_Assets",
                                                       "HE_CertificatesOfImmunity")
    eh_buildingPreservationNoticesPointsPath = os.path.join(geodatabase, "Designated_Heritage_Assets",
                                                            "HE_BuildingPreservationNotices")
    # Heritage at Risk
    eh_heritageAtRisk_ArchaeologyAssessmentAreasPath = os.path.join(geodatabase, "Designated_Heritage_Assets",
                                                                    "HE_HAR_ArchaeologyAssessmentAreas")
    eh_heritageAtRisk_BattlefieldAssessmentAreasPath = os.path.join(geodatabase, "Designated_Heritage_Assets",
                                                                    "HE_HAR_BattlefieldAssessmentAreas")
    eh_heritageAtRisk_BuildingOrStructureAssessmentAreasPath = os.path.join(geodatabase, "Designated_Heritage_Assets",
                                                                            "HE_HAR_BuildingOrStructureAssessmentAreas")
    eh_heritageAtRisk_BuildingOrStructureAssessmentListedBuildingsPath = os.path.join(geodatabase,
                                                                                      "Designated_Heritage_Assets",
                                                                                      "HE_HAR_BuildingOrStructureAssessmentListedBuildings")
    eh_heritageAtRisk_ConservationAreaAssessmentAreasPath = os.path.join(geodatabase, "Designated_Heritage_Assets",
                                                                         "HE_HAR_ConservationAreaAssessmentAreas")
    eh_heritageAtRisk_ParkandGardenAssessmentAreasPath = os.path.join(geodatabase, "Designated_Heritage_Assets",
                                                                      "HE_HAR_ParkandGardenAssessmentAreas")
    eh_heritageAtRisk_PlaceOfWorshipAssessmentListedBuildingsPath = os.path.join(geodatabase,
                                                                                 "Designated_Heritage_Assets",
                                                                                 "HE_HAR_PlaceOfWorshipAssessmentListedBuildings")
    # ----------------------------------------------------------------------------------------------------------------------
    # --- Output paths for Welsh data --------------------------------------------------------------------------------------
    cadw_caPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "Cadw_ConservationAreas")
    cadw_hlaPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "Cadw_HistoricLandscapeAreas")
    cadw_listedBuildingPointPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "Cadw_ListedBuildings")
    cadw_parksGardensPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "Cadw_ParksGardens")
    cadw_scheduledMonumentsPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets",
                                                      "Cadw_ScheduledMonuments")
    cadw_worldHeritageSitesPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets",
                                                      "Cadw_WorldHeritageSites")
    # Landmap data
    landmapCulturalPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "CCW_Landmap_CulturalLandscape")
    landmapHistoricPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "CCW_Landmap_HistoricLandscape")
    landmapVisSensPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "CCW_Landmap_VIsualSensory")
    # ----------------------------------------------------------------------------------------------------------------------
    # --- Scottish designations data ---------------------------------------------------------------------------------------
    hs_battlefieldPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HS_Battlefields")
    hs_conservationAreasPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HS_ConservationAreas")
    hs_listedBuildingPointPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HS_ListedBuildings")
    hs_gardensDesignedLandscapesPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets",
                                                           "HS_GardensDesignedLandscapes")
    hs_scheduledMonumentsPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HS_ScheduledMonuments")
    hs_worldHeritageSitesPolygonPath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HS_WorldHeritageSites")
    hs_propertiesInCarePath = os.path.join(geodatabase, "Designated_Heritage_Assets", "HS_PropertiesInCare")
    # ----------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    if inEngland == 1:
        # Set up paths --------------------------------------------------------------
        bfPath = "K:\GIS\Data\HistoricEngland\Battlefields\Battlefields.shp"
        lbPtPath = "K:\GIS\Data\HistoricEngland\Listed Buildings\ListedBuildings.shp"
        pgPath = "K:\GIS\Data\HistoricEngland\Parks and Gardens\ParksAndGardens.shp"
        smPath = "K:\GIS\Data\HistoricEngland\Scheduled Monuments\ScheduledMonuments.shp"
        whPath = "K:\GIS\Data\HistoricEngland\World Heritage Sites\WorldHeritageSites.shp"
        ciPath = "K:\GIS\Data\HistoricEngland\Certificates Of Immunity\CertificatesOfImmunity.shp"
        bpnPath = "K:\GIS\Data\HistoricEngland\Building Preservation Notices\BuildingPreservationNotices.shp"
        harAAAPath = "K:\GIS\Data\HistoricEngland\HeritageAtRisk\Archaeology_Assessment_Areas.shp"
        harBAAPath = "K:\GIS\Data\HistoricEngland\HeritageAtRisk\Battlefield_Assessment_Areas.shp"
        harBSAAPath = "K:\GIS\Data\HistoricEngland\HeritageAtRisk\BuildingOrStructure_Assessment_ListedBuildings.shp"
        harCAAPath = "K:\GIS\Data\HistoricEngland\HeritageAtRisk\ConservationArea_Assessment.shp"
        harPGAAPath = "K:\GIS\Data\HistoricEngland\HeritageAtRisk\ParkandGarden_Assessment_Areas.shp"
        harPoWALBPath = "K:\GIS\Data\HistoricEngland\HeritageAtRisk\PlaceOfWorship_Assessment_ListedBuildings.shp"
        harBSAALBPath = "K:\GIS\Data\HistoricEngland\HeritageAtRisk\BuildingOrStructure_Assessment_ListedBuildings.shp"
        # ---------------------------------------------------------------------------------------------------
        # Make feature layers for spatial selecting ---------------------------------------------------------
        arcpy.MakeFeatureLayer_management(bfPath, "Battlefields_lyr_HE")
        arcpy.MakeFeatureLayer_management(lbPtPath, "ListedBuildings_lyr_HE")
        arcpy.MakeFeatureLayer_management(pgPath, "ParksGardens_lyr_HE")
        arcpy.MakeFeatureLayer_management(smPath, "ScheduledMonuments_lyr_HE")
        arcpy.MakeFeatureLayer_management(whPath, "WorldHeritageSites_lyr_HE")
        arcpy.MakeFeatureLayer_management(ciPath, "certificatesOfImmunity_lyr_HE")
        arcpy.MakeFeatureLayer_management(bpnPath, "buildingPreservationNotices_lyr_HE")
        arcpy.MakeFeatureLayer_management(harAAAPath, "archaeologyAssessmentAreas_lyr_HE")
        arcpy.MakeFeatureLayer_management(harBAAPath, "battlefieldAssessmentAreas_lyr_HE")
        arcpy.MakeFeatureLayer_management(harBSAAPath, "buildingOrStructureAssessmentAreas_lyr_HE")
        arcpy.MakeFeatureLayer_management(harBSAALBPath, "buildingOrStructureAssessmentListedBuildings_lyr_HE")
        arcpy.MakeFeatureLayer_management(harCAAPath, "conservationArea_Assessment_lyr_HE")
        arcpy.MakeFeatureLayer_management(harPGAAPath, "parkandGardenAssessmentAreas_lyr_HE")
        arcpy.MakeFeatureLayer_management(harPoWALBPath, "placeOfWorshipAssessmentListedBuildings_lyr_HE")
        # ---------------------------------------------------------------------------------------------------

    if inEngland == 1:
        # Select designated sites within the study area -----------------------------------------------------
        # Selections and outputs (if features exist)
        arcpy.SetProgressorLabel("Extracting designations data for the study area")

        # Battlefields
        arcpy.SetProgressorLabel("Extracting Battlefields data")
        arcpy.SelectLayerByLocation_management("Battlefields_lyr_HE", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("Battlefields_lyr_HE")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Battlefields")
        else:
            arcpy.CopyFeatures_management("Battlefields_lyr_HE", eh_battlefieldPolygonPath)

        # Listed Buildings
        arcpy.SetProgressorLabel("Extracting Listed Buildings data")
        arcpy.SelectLayerByLocation_management("ListedBuildings_lyr_HE", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("ListedBuildings_lyr_HE")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Listed Buildings")
        else:
            arcpy.CopyFeatures_management("ListedBuildings_lyr_HE", eh_listedBuildingPointPath)

        # Parks and Gardens
        arcpy.SetProgressorLabel("Extracting Parks and Gardens data")
        arcpy.SelectLayerByLocation_management("ParksGardens_lyr_HE", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("ParksGardens_lyr_HE")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Parks and Gardens")
        else:
            arcpy.CopyFeatures_management("ParksGardens_lyr_HE", eh_parksGardensPolygonPath)

        # Scheduled Monuments
        arcpy.SetProgressorLabel("Extracting Scheduled Monuments data")
        arcpy.SelectLayerByLocation_management("ScheduledMonuments_lyr_HE", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("ScheduledMonuments_lyr_HE")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Scheduled Monuments")
        else:
            arcpy.CopyFeatures_management("ScheduledMonuments_lyr_HE", eh_scheduledMonumentsPolygonPath)

        # World Heritage Sites
        arcpy.SetProgressorLabel("Extracting World Heritage Sites data")
        arcpy.SelectLayerByLocation_management("WorldHeritageSites_lyr_HE", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("WorldHeritageSites_lyr_HE")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No World Heritage Sites")
        else:
            arcpy.CopyFeatures_management("WorldHeritageSites_lyr_HE", eh_worldHeritageSitesPolygonPath)

        # Certificates of Immunity
        arcpy.SetProgressorLabel("Extracting Certificates of Immunity data")
        arcpy.SelectLayerByLocation_management("certificatesOfImmunity_lyr_HE", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("certificatesOfImmunity_lyr_HE")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Certificates of Immunity")
        else:
            arcpy.CopyFeatures_management("certificatesOfImmunity_lyr_HE", eh_certificatesOfImmunityPointsPath)

        # Building Preservation Notices
        arcpy.SetProgressorLabel("Extracting Building Preservation Notices data")
        arcpy.SelectLayerByLocation_management("buildingPreservationNotices_lyr_HE", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("buildingPreservationNotices_lyr_HE")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Building Preservation Notices")
        else:
            arcpy.CopyFeatures_management("buildingPreservationNotices_lyr_HE",
                                          eh_buildingPreservationNoticesPointsPath)

            # Heritage at Risk
            arcpy.SetProgressorLabel("Extracting Heritage at Risk Register data")
            arcpy.SelectLayerByLocation_management("archaeologyAssessmentAreas_lyr_HE", "INTERSECT", "searchArea_lyr")
            featuresCount = arcpy.GetCount_management("archaeologyAssessmentAreas_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No HAR Archaeology Assessment Areas")
            else:
                arcpy.CopyFeatures_management("archaeologyAssessmentAreas_lyr_HE",
                                              eh_heritageAtRisk_ArchaeologyAssessmentAreasPath)

            arcpy.SelectLayerByLocation_management("battlefieldAssessmentAreas_lyr_HE", "INTERSECT", "searchArea_lyr")
            featuresCount = arcpy.GetCount_management("battlefieldAssessmentAreas_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No HAR Battlefield Assessment Areas")
            else:
                arcpy.CopyFeatures_management("battlefieldAssessmentAreas_lyr_HE",
                                              eh_heritageAtRisk_BattlefieldAssessmentAreasPath)

            arcpy.SelectLayerByLocation_management("buildingOrStructureAssessmentAreas_lyr_HE", "INTERSECT",
                                                   "searchArea_lyr")
            featuresCount = arcpy.GetCount_management("buildingOrStructureAssessmentAreas_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No HAR Building or Structure Assessment Areas")
            else:
                arcpy.CopyFeatures_management("buildingOrStructureAssessmentAreas_lyr_HE",
                                              eh_heritageAtRisk_BuildingOrStructureAssessmentAreasPath)

            arcpy.SelectLayerByLocation_management("buildingOrStructureAssessmentListedBuildings_lyr_HE", "INTERSECT",
                                                   "searchArea_lyr")
            featuresCount = arcpy.GetCount_management("buildingOrStructureAssessmentListedBuildings_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No HAR Building or Structure Assessment Areas (Listed Buildings)")
            else:
                arcpy.CopyFeatures_management("buildingOrStructureAssessmentListedBuildings_lyr_HE",
                                              eh_heritageAtRisk_BuildingOrStructureAssessmentListedBuildingsPath)

            arcpy.SelectLayerByLocation_management("conservationArea_Assessment_lyr_HE", "INTERSECT", "searchArea_lyr")
            featuresCount = arcpy.GetCount_management("conservationArea_Assessment_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No HAR Conservation Area Assessment Areas")
            else:
                arcpy.CopyFeatures_management("conservationArea_Assessment_lyr_HE",
                                              eh_heritageAtRisk_ConservationAreaAssessmentAreasPath)

            arcpy.SelectLayerByLocation_management("parkandGardenAssessmentAreas_lyr_HE", "INTERSECT", "searchArea_lyr")
            featuresCount = arcpy.GetCount_management("parkandGardenAssessmentAreas_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No HAR Park and Garden Assessment Areas")
            else:
                arcpy.CopyFeatures_management("parkandGardenAssessmentAreas_lyr_HE",
                                              eh_heritageAtRisk_ParkandGardenAssessmentAreasPath)

            arcpy.SelectLayerByLocation_management("placeOfWorshipAssessmentListedBuildings_lyr_HE", "INTERSECT",
                                                   "searchArea_lyr")
            featuresCount = arcpy.GetCount_management("placeOfWorshipAssessmentListedBuildings_lyr_HE")
            if str(featuresCount) == "0":
                arcpy.AddMessage("No HAR Place of Worship (Listed Buildings) Assessment Areas")
            else:
                arcpy.CopyFeatures_management("placeOfWorshipAssessmentListedBuildings_lyr_HE",
                                              eh_heritageAtRisk_PlaceOfWorshipAssessmentListedBuildingsPath)
    if inScotland == 1:
        # Set up paths --------------------------------------------------------------------------------------
        bfPath = "K:\GIS\Data\HistoricScotland\BattlefieldsInventory\Battlefields_inventory_boundary.shp"
        caPath = "K:\GIS\Data\HistoricScotland\ConservationAreas\Conservation_Areas.shp"
        lbPtPath = "K:\GIS\Data\HistoricScotland\ListedBuildings\Listed_Buildings.shp"
        gdlPath = "K:\GIS\Data\HistoricScotland\GardensAndDesignedLandscapes\Gardens_and_Designed_Landscapes.shp"
        smPath = "K:\GIS\Data\HistoricScotland\ScheduledMonuments\Scheduled_Monuments.shp"
        whPath = "K:\GIS\Data\HistoricScotland\WorldHeritageSites\World_Heritage_Sites.shp"
        picPath = "K:\GIS\Data\HistoricScotland\PropertiesInCare\Properties_in_care.shp"
        # ---------------------------------------------------------------------------------------------------
        # Make feature layers for spatial selecting ---------------------------------------------------------
        arcpy.MakeFeatureLayer_management(bfPath, "Battlefields_lyr_HS")
        arcpy.MakeFeatureLayer_management(caPath, "ConservationAreas_lyr_HS")
        arcpy.MakeFeatureLayer_management(lbPtPath, "ListedBuildings_lyr_HS")
        arcpy.MakeFeatureLayer_management(gdlPath, "gardensDesignedLandscapes_lyr_HS")
        arcpy.MakeFeatureLayer_management(smPath, "ScheduledMonuments_lyr_HS")
        arcpy.MakeFeatureLayer_management(whPath, "WorldHeritageSites_lyr_HS")
        arcpy.MakeFeatureLayer_management(whPath, "PropertiesInCare_lyr_HS")
        # ---------------------------------------------------------------------------------------------------
    if inScotland == 1:
        # Select designated sites within the study area -----------------------------------------------------
        # Selections and outputs (if features exist)
        arcpy.SetProgressorLabel("Extracting designations data for the study area")

        # Battlefields
        arcpy.SetProgressorLabel("Extracting Battlefields data")
        arcpy.SelectLayerByLocation_management("Battlefields_lyr_HS", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("Battlefields_lyr_HS")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Battlefields")
        else:
            arcpy.CopyFeatures_management("Battlefields_lyr_HS", hs_battlefieldPolygonPath)

        # Conservation areas
        arcpy.SetProgressorLabel("Extracting Conservation Areas data")
        arcpy.SelectLayerByLocation_management("ConservationAreas_lyr_HS", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("ConservationAreas_lyr_HS")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Conservation Areas")
        else:
            arcpy.CopyFeatures_management("ConservationAreas_lyr_HS", hs_conservationAreasPath)

        # Listed Buildings
        arcpy.SetProgressorLabel("Extracting Listed Buildings data")
        arcpy.SelectLayerByLocation_management("ListedBuildings_lyr_HS", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("ListedBuildings_lyr_HS")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Listed Buildings")
        else:
            arcpy.CopyFeatures_management("ListedBuildings_lyr_HS", hs_listedBuildingPointPath)

        # Gardens and Designed Landscapes
        arcpy.SetProgressorLabel("Extracting Gardens and Designed Landscapes data")
        arcpy.SelectLayerByLocation_management("gardensDesignedLandscapes_lyr_HS", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("gardensDesignedLandscapes_lyr_HS")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Gardens and Designed Landscapes")
        else:
            arcpy.CopyFeatures_management("gardensDesignedLandscapes_lyr_HS", hs_gardensDesignedLandscapesPolygonPath)

        # Scheduled Monuments
        arcpy.SetProgressorLabel("Extracting scheduled monuments data")
        arcpy.SelectLayerByLocation_management("ScheduledMonuments_lyr_HS", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("ScheduledMonuments_lyr_HS")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Scheduled Monuments")
        else:
            arcpy.CopyFeatures_management("ScheduledMonuments_lyr_HS", hs_scheduledMonumentsPolygonPath)

        # World Heritage Sites
        arcpy.SetProgressorLabel("Extracting WHS data")
        arcpy.SelectLayerByLocation_management("WorldHeritageSites_lyr_HS", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("WorldHeritageSites_lyr_HS")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No World Heritage Sites")
        else:
            arcpy.CopyFeatures_management("WorldHeritageSites_lyr_HS", hs_worldHeritageSitesPolygonPath)

        # Properties in Care
        arcpy.SetProgressorLabel("Extracting Properties in Care data")
        arcpy.SelectLayerByLocation_management("PropertiesInCare_lyr_HS", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("PropertiesInCare_lyr_HS")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Properties in Care")
        else:
            arcpy.CopyFeatures_management("PropertiesInCare_lyr_HS", hs_worldHeritageSitesPolygonPath)
    # ----------------------------------------------------------------------------------------------------------------
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
        # ----------------------------------------------------------------------------------------------------------------------------

    if inWales == 1:
        # Selections and outputs (if features exist) ---------------------------------------------------------------------------------
        arcpy.SetProgressorLabel("Extracting designations data for the study area")

        # CAs
        arcpy.SetProgressorLabel("Extracting Conservation Areas data")
        arcpy.SelectLayerByLocation_management("ConservationAreas_lyr_Cadw", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("ConservationAreas_lyr_Cadw")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Conservation Areas")
        else:
            arcpy.CopyFeatures_management("ConservationAreas_lyr_Cadw", cadw_hlaPolygonPath)

        # HLAs
        arcpy.SetProgressorLabel("Extracting Historic Landscape Areas data")
        arcpy.SelectLayerByLocation_management("HistoricLandscapeAreas_lyr_Cadw", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("HistoricLandscapeAreas_lyr_Cadw")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Historic Landscape Areas")
        else:
            arcpy.CopyFeatures_management("HistoricLandscapeAreas_lyr_Cadw", cadw_hlaPolygonPath)

        # Listed Buildings
        arcpy.SetProgressorLabel("Extracting Listed Buildings data")
        arcpy.SelectLayerByLocation_management("ListedBuildings_lyr_Cadw", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("ListedBuildings_lyr_Cadw")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Listed Buildings")
        else:
            arcpy.CopyFeatures_management("ListedBuildings_lyr_Cadw", cadw_listedBuildingPointPath)

        # Parks and Gardens
        arcpy.SetProgressorLabel("Extracting Parks and Gardens data")
        arcpy.SelectLayerByLocation_management("ParksGardens_lyr_Cadw", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("ParksGardens_lyr_Cadw")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Parks and Gardens")
        else:
            arcpy.CopyFeatures_management("ParksGardens_lyr_Cadw", cadw_parksGardensPolygonPath)

        # Scheduled Monuments
        arcpy.SetProgressorLabel("Extracting Scheduled Monuments data")
        arcpy.SelectLayerByLocation_management("ScheduledMonuments_lyr_Cadw", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("ScheduledMonuments_lyr_Cadw")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Scheduled Monuments")
        else:
            arcpy.CopyFeatures_management("ScheduledMonuments_lyr_Cadw", cadw_scheduledMonumentsPolygonPath)

        # World Heritage Sites
        arcpy.SetProgressorLabel("Extracting World Heritage Sites data")
        arcpy.SelectLayerByLocation_management("WorldHeritageSites_lyr_Cadw", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("WorldHeritageSites_lyr_Cadw")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No World Heritage Sites")
        else:
            arcpy.CopyFeatures_management("WorldHeritageSites_lyr_Cadw", cadw_worldHeritageSitesPolygonPath)

        # Landmap - Cultural Landscape
        arcpy.SetProgressorLabel("Extracting Landmap (Cultural Landscape) data")
        arcpy.SelectLayerByLocation_management("CulturalLandscape_lyr", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("CulturalLandscape_lyr")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Landmap (Cultural Landscape) data")
        else:
            arcpy.CopyFeatures_management("CulturalLandscape_lyr", landmapCulturalPath)

        # Landmap - Historic Landscape
        arcpy.SetProgressorLabel("Extracting Landmap (Historic Landscape) data")
        arcpy.SelectLayerByLocation_management("HistoricLandscape_lyr", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("HistoricLandscape_lyr")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Landmap (Historic Landscape) data")
        else:
            arcpy.CopyFeatures_management("HistoricLandscape_lyr", landmapHistoricPath)

        # Landmap - Visual Sensory
        arcpy.SetProgressorLabel("Extracting Landmap (Visual Sensory) data")
        arcpy.SelectLayerByLocation_management("VisualSensory_lyr", "INTERSECT", "searchArea_lyr")
        featuresCount = arcpy.GetCount_management("VisualSensory_lyr")
        if str(featuresCount) == "0":
            arcpy.AddMessage("No Landmap (Visual Sensory) data")
        else:
            arcpy.CopyFeatures_management("VisualSensory_lyr", landmapVisSensPath)
            # ----------------------------------------------------------------------------------------------------------------------------

    # --- Extract previous projects data -----------------------------------------------------------------------------------------
    arcpy.SetProgressorLabel("Extracting previous projects (Sales Pipeline) data")

    arcpy.SelectLayerByLocation_management("studyAreas_lyr", "INTERSECT", "searchArea_lyr", "1000")
    featuresCount = arcpy.GetCount_management("studyAreas_lyr")
    if str(featuresCount) == "0":
        arcpy.AddMessage("No WA study areas in the vicinity")
    else:
        arcpy.CopyFeatures_management("studyAreas_lyr", outputStudyAreas)

    arcpy.SelectLayerByLocation_management("projectCentroids_lyr", "INTERSECT", "searchArea_lyr", "1000")
    featuresCount = arcpy.GetCount_management("projectCentroids_lyr")
    if str(featuresCount) == "0":
        arcpy.AddMessage("No WA project centroids in the vicinity")
    else:
        arcpy.CopyFeatures_management("projectCentroids_lyr", outputProjectCentroids)

    arcpy.SelectLayerByLocation_management("siteBoundaries_lyr", "INTERSECT", "searchArea_lyr", "1000")
    featuresCount = arcpy.GetCount_management("siteBoundaries_lyr")
    if str(featuresCount) == "0":
        arcpy.AddMessage("No WA project site boundaries in the vicinity")
    else:
        arcpy.CopyFeatures_management("siteBoundaries_lyr", outputSiteBoundaries)

    arcpy.SelectLayerByLocation_management("otherAreas_lyr", "INTERSECT", "searchArea_lyr", "1000")
    featuresCount = arcpy.GetCount_management("otherAreas_lyr")
    if str(featuresCount) == "0":
        arcpy.AddMessage("No WA 'other areas' in the vicinity")
    else:
        arcpy.CopyFeatures_management("otherAreas_lyr", outputOtherAreas)

    arcpy.SelectLayerByLocation_management("excavatedAreas_lyr", "INTERSECT", "searchArea_lyr", "1000")
    featuresCount = arcpy.GetCount_management("excavatedAreas_lyr")
    if str(featuresCount) == "0":
        arcpy.AddMessage("No WA excavated areas in the vicinity")
    else:
        arcpy.CopyFeatures_management("excavatedAreas_lyr", outputExcavatedAreas)

    arcpy.SelectLayerByLocation_management("evalTrenches_lyr", "INTERSECT", "searchArea_lyr", "1000")
    featuresCount = arcpy.GetCount_management("evalTrenches_lyr")
    if str(featuresCount) == "0":
        arcpy.AddMessage("No WA evaluation trenches or test pits in the vicinity")
    else:
        arcpy.CopyFeatures_management("evalTrenches_lyr", outputEvalTrenches)

    # ----------------------------------------------------------------------------

    # --- Copy the template MXD --------------------------------------------------------------------------------------------------
    arcpy.SetProgressorLabel("Copying the template MXD")
    # --- Template source ---------
    srcMXD = "K:/GIS/_Templates/Heritage.mxd"
    # -----------------------------
    # Create destination path
    dstMXDName = projectNumber + "_" + siteName + "_Setup.mxd"
    dstMXD = os.path.join(GISFolder, "SetupMXD", dstMXDName)
    shutil.copy(srcMXD, dstMXD)

    # Copy input location to site folder
    siteBoundary = siteName + "_" + projectNumber + "_SiteBoundary"
    siteBoundaryPath = os.path.join(geodatabase, "Site_and_StudyArea", siteBoundary)
    arcpy.MakeFeatureLayer_management(inLocation, "siteBoundary_lyr")
    arcpy.CopyFeatures_management("siteBoundary_lyr", siteBoundaryPath)

    # -------------------------------------#

    arcpy.SetProgressorLabel("Setting the MXD links...")
    arcpy.AddMessage("Setting the MXD links...")

    # ---------------------------------------------#
    mxd = arcpy.mapping.MapDocument(dstMXD)
    # Get data frame for removing and updating layers
    df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]

    # Loop through layers - remove or fix sources
    arcpy.SetProgressorLabel("Setting the site and study area links...")
    arcpy.AddMessage("Setting the site and study area links...")
    for lyr in arcpy.mapping.ListLayers(mxd):
        # Remove layers from MXD if the shapefiles weren't created
        # Check the geometry of the site and remove layers
        if lyr.name == "Site (point)":
            if inLocationGeometry == "Point":
                lyr.name = "Site"
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", siteBoundary)
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Site (line)":
            if inLocationGeometry == "Polyline":
                lyr.name = "Site"
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", siteBoundary)
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Site (polygon)":
            if inLocationGeometry == "Polygon":
                lyr.name = "Site"
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", siteBoundary)
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Study Area":
            lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", (siteName + "_" + projectNumber + "_StudyArea"))

            df.zoomToSelectedFeatures()

    # Check designations - change sources or remove layers
    arcpy.SetProgressorLabel("Setting the designated heritage assets links...")
    arcpy.AddMessage("Setting the designated heritage assets links....")
    for lyr in arcpy.mapping.ListLayers(mxd):

        if lyr.name == "Historic England Listed Buildings":
            if arcpy.Exists(eh_listedBuildingPointPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_ListedBuildings")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)

        if lyr.name == "Historic England Scheduled Monuments":
            if arcpy.Exists(eh_scheduledMonumentsPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_ScheduledMonuments")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)

        if lyr.name == "Historic England Parks and Gardens":
            if arcpy.Exists(eh_parksGardensPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_ParksGardens")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)

        if lyr.name == "Historic England Battlefields":
            if arcpy.Exists(eh_battlefieldPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_Battlefields")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)

        if lyr.name == "Historic England World Heritage Sites":
            if arcpy.Exists(eh_worldHeritageSitesPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_WorldHeritageSites")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic England Building Preservation Notices":
            if arcpy.Exists(eh_buildingPreservationNoticesPointsPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_BuildingPreservationNotices")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic England Certificates of Immunity":
            if arcpy.Exists(eh_certificatesOfImmunityPointsPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_CertificatesOfImmunity")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic England HAR Register - Archaeology Assessment Areas":
            if arcpy.Exists(eh_heritageAtRisk_ArchaeologyAssessmentAreasPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_HAR_ArchaeologyAssessmentAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic England HAR Register - Battlefield Assessment Areas":
            if arcpy.Exists(eh_heritageAtRisk_BattlefieldAssessmentAreasPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_HAR_BattlefieldAssessmentAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic England HAR Register - Building or Structure Assessment Areas":
            if arcpy.Exists(eh_heritageAtRisk_BuildingOrStructureAssessmentAreasPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_HAR_BuildingOrStructureAssessmentAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic England HAR Register - Building or Structure Assessment (Listed Buildings)":
            if arcpy.Exists(eh_heritageAtRisk_BuildingOrStructureAssessmentListedBuildingsPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE",
                                      "HE_HAR_BuildingOrStructureAssessmentListedBuildings")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic England HAR Register - Conservation Assessment Areas":
            if arcpy.Exists(eh_heritageAtRisk_ConservationAreaAssessmentAreasPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_HAR_ConservationAreaAssessmentAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic England HAR Register - Park and Garden Assessment Areas":
            if arcpy.Exists(eh_heritageAtRisk_ParkandGardenAssessmentAreasPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HE_HAR_ParkandGardenAssessmentAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic England HAR Register - Place of Worship Assessment (Listed Buildings)":
            if arcpy.Exists(eh_heritageAtRisk_PlaceOfWorshipAssessmentListedBuildingsPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE",
                                      "HE_HAR_PlaceOfWorshipAssessmentListedBuildings")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)

        if lyr.name == "Cadw Listed Buildings":
            if arcpy.Exists(cadw_listedBuildingPointPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "Cadw_ListedBuildings")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Cadw Historic Landscapes Areas":
            if arcpy.Exists(cadw_hlaPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "Cadw_HistoricLandscapeAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Cadw Parks":
            if arcpy.Exists(cadw_parksGardensPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "Cadw_ParksGardens")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Cadw Scheduled Monuments":
            if arcpy.Exists(cadw_scheduledMonumentsPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "Cadw_ScheduledMonuments")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Cadw World Heritage Sites":
            if arcpy.Exists(cadw_worldHeritageSitesPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "Cadw_WorldHeritageSites")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Welsh Conservation Areas":
            if arcpy.Exists(cadw_caPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "WelshConservationAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "CCW Landmap - Cultural Landscape":
            if arcpy.Exists(landmapCulturalPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "CCW_Landmap_CulturalLandscape")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "CCW Landmap - Historic Landscape":
            if arcpy.Exists(landmapHistoricPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "CCW_Landmap_HistoricLandscape")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "CCW Landmap - Visual-Sensory":
            if arcpy.Exists(landmapVisSensPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "CCW_Landmap_VisualSensory")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)

        if lyr.name == "Historic Environment Scotland Battlefields":
            if arcpy.Exists(hs_battlefieldPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HS_Battlefields")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic Environment Scotland Conservation Areas":
            if arcpy.Exists(hs_conservationAreasPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HS_ConservationAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic Environment Scotland Gardens and Designed Landscapes":
            if arcpy.Exists(hs_gardensDesignedLandscapesPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HS_GardensDesignedLandscapes")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic Environment Scotland Listed Buildings":
            if arcpy.Exists(hs_listedBuildingPointPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HS_ListedBuildings")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic Environment Scotland Properties in Care":
            if arcpy.Exists(hs_propertiesInCarePath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HS_PropertiesInCare")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic Environment Scotland Scheduled Monuments":
            if arcpy.Exists(hs_scheduledMonumentsPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HS_ScheduledMonuments")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Historic Environment Scotland World Heritage Sites":
            if arcpy.Exists(hs_worldHeritageSitesPolygonPath):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "HS_WorldHeritageSites")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)

    # Check WA Project Data
    arcpy.SetProgressorLabel("Setting the WA project links...")
    arcpy.AddMessage("Setting the WA project links....")
    for lyr in arcpy.mapping.ListLayers(mxd):

        if lyr.name == "Centroids":
            if arcpy.Exists(outputProjectCentroids):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "WA_ProjectCentroids")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Study areas":
            if arcpy.Exists(outputStudyAreas):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "WA_StudyAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Site boundaries":
            if arcpy.Exists(outputSiteBoundaries):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "WA_SiteBoundaries")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Other areas":
            if arcpy.Exists(outputOtherAreas):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "WA_OtherAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Excavated areas":
            if arcpy.Exists(outputExcavatedAreas):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "WA_ExcavatedAreas")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)
        if lyr.name == "Eval trenches and test pits":
            if arcpy.Exists(outputEvalTrenches):
                lyr.replaceDataSource(geodatabase, "FILEGDB_WORKSPACE", "WA_EvalTrenches")
            else:
                arcpy.mapping.RemoveLayer(df, lyr)

        # Check for HER boundaries
        if lyr.name == "HERs":
            lyr.replaceDataSource("K:/GIS/Data/HERs/SHP", "SHAPEFILE_WORKSPACE", "HERs")

        if lyr.name == "NMP areas":
            lyr.replaceDataSource("K:/GIS/Data/MappingProjects/NMPAreas", "SHAPEFILE_WORKSPACE", "NMPAreas")
        if lyr.name == "Intermediary areas":
            lyr.replaceDataSource("K:/GIS/Data/MappingProjects/DomesdayShires&Hundreds/SHP", "SHAPEFILE_WORKSPACE",
                                  "IntermediaryAreas")
        if lyr.name == "Shires":
            lyr.replaceDataSource("K:/GIS/Data/MappingProjects/DomesdayShires&Hundreds/SHP", "SHAPEFILE_WORKSPACE",
                                  "Shires")
        if lyr.name == "Hundreds":
            lyr.replaceDataSource("K:/GIS/Data/MappingProjects/DomesdayShires&Hundreds/SHP", "SHAPEFILE_WORKSPACE",
                                  "Hundreds")

    # Save the MXD
    mxd.save()

    # add new columns to siteboundary and study area
    arcpy.AddField_management(searchArea, "Description", "TEXT", field_length=100, field_is_nullable="NULLABLE")
    arcpy.management.EnableEditorTracking(searchArea, "Creator", "Created", "Editor", "Edited", "ADD_FIELDS",
                                          "DATABASE_TIME")
    arcpy.AddField_management(siteBoundaryPath, "Description", "TEXT", field_length=100, field_is_nullable="NULLABLE")
    arcpy.management.EnableEditorTracking(siteBoundaryPath, "Creator", "Created", "Editor", "Edited", "ADD_FIELDS",
                                          "DATABASE_TIME")
    # Delete working folders
    arcpy.SetProgressorLabel("Clearing up...")
    arcpy.AddMessage("Clearing up...")

    arcpy.Delete_management(workingVector)
    arcpy.Delete_management(workingRaster)
    arcpy.Delete_management(rasterFolder)
    arcpy.Delete_management(shpFolder)




except Exception as e:
    arcpy.AddError(e)
