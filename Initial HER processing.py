# This script is designed to process raw HER data. It will add and calculate the easting, northing and distance from the designated "site"
# boundary. Once this is complete the script will remove redundant fields add a "periodFrom" field and calculate the value for the field
# based on a designated value 

import arcpy

# User Input 1 - Shapefile to be calculated
featureClass = arcpy.GetParameterAsText(0)
# User Inpit 2 - site boundary
siteBoundary = arcpy.GetParameterAsText(1)
# user Input 3 - PeriodFrom required?
periodFrom = arcpy.GetParameterAsText(2)
# user Input 4 - state whether periodFrom is required and what column to use (Period, PeriodRang, DateRang, not required)
fcColumn = arcpy.GetParameterAsText(3)
# user Input 5 - select which existing layer to use for the symbology (Points, Polygons, Lines)
symbology = arcpy.GetParameterAsText(4)

# location of the symbology layers

try:
    # Set enviroment settings
    arcpy.env.workspace = featureClass
    arcpy.env.overwriteOutput = True

    # Variables
    fieldName1 = "Easting"
    fieldName2 = "Northing"
    fieldName3 = "NEAR_DIST"
    fieldname4 = "PeriodFrom"
    fieldPrecision = 6
    fieldLength = 50
    fieldLength2 = 50
    searchRadius = "5000 Meters"

    # List all fields in the attribute table
    fieldNameList = [field.name for field in arcpy.ListFields(featureClass)]

    # If PeriodFrom field is required
    if periodFrom == "Yes":
        arcpy.AddField_management(featureClass, "PeriodFrom", "TEXT", "", "", fieldLength)
        arcpy.AddMessage("periodFrom added")
    else:
        arcpy.AddMessage("PeriodFrom not required")

    # If the Easting field exists
    if fieldName1 in fieldNameList:
        arcpy.AddMessage("Easting field already exists")
    else:
        # Add Easting field
        arcpy.AddField_management(featureClass, fieldName1, "LONG", fieldPrecision)
        arcpy.AddMessage("Easting field added")

        # Calculate Eastings
        arcpy.CalculateField_management(featureClass, fieldName1, "!SHAPE.CENTROID.X!", "PYTHON_9.3")
        arcpy.AddMessage("Eastings calculated")

    # If the Northing field exists
    if fieldName2 in fieldNameList:
        arcpy.AddMessage("Northing field already exists")
    else:
        # Add Northing field
        arcpy.AddField_management(featureClass, fieldName2, "LONG", fieldPrecision)
        arcpy.AddMessage("Northing field added")
        # Calculate Northing
        arcpy.CalculateField_management(featureClass, fieldName2, "!SHAPE.CENTROID.Y!", "PYTHON_9.3")
        arcpy.AddMessage("Northings calculated")

    # If NEAR_DIST field exists
    if fieldName3 in fieldNameList:
        arcpy.AddMessage("Distance to Site Boundary already calculated")
    else:
        arcpy.Near_analysis(featureClass, siteBoundary, searchRadius)
        arcpy.AddMessage("Distance to Site Boundary calculated")

    # Delete fields from the HER shapefiles that are not required
    arcpy.DeleteField_management(featureClass,
                                 ["condition", "status", "status gra", "status ref", "unitary au", "Community",
                                  "SiteAltern","SiteStat_1","SiteWebsit","SiteStat_2","SiteStat_3","SiteHeight",
                                  "Created_us","Created_da","eastings", "northings", "map sheet","MI_PRINX", "Ref",
                                  "Organisati", "DispDate", "FeatureDes", "Representa", "QualityNot","MinFrom",
                                  "MaxTo", "MonType", "Dates", "CapturePro", "CaptureSca", "SourcePrec", "Accuracy",
                                  "Height", "Validation", "BufferZone","MI_STYLE", "Finds", "WhenCreate", "CreatedBy",
                                  "WhenLastEd", "_MONRecord","_YearMin", "_YearMax", "_MonTypes","Period2","Period3",
                                  "GridRef", "MapSheet", "_Topology","Topology", "InputPrec", "_MixX", "_MinY", "_MaxX",
                                  "_MaxY","_NGRQaulif", "LastEdited", "MI_STYLE", "XgGeometry","Height_1","MonUID_1",
                                  "PreRef_1", "RecordTy_1", "Name_1", "xgGeometry", "MinFrom", "MaxTo","Minx","MinY",
                                  "MaxX","MaxY","Form","Land_Use","Drif_Geol","Ownershhip_","Site_Aspec","Compiled_B",
                                  "Date_Compi","Last_Edite","Date_Alter","Legal_Stat","Legal_St_1","Legal_St_2",
                                  "Legal_St_3","Legal_St_4", "Legal_ST_5","Visit1","Date1","Desc1","Visit2","Date2",
                                  "Desc2","Visit3","Date3","Desc3","Visit4","Date4","Desc4","Visit5","Date5","Desc5",
                                  "Visit6","Date6","Desc6","type","Broad clas","evidence","community","ngr","BROADCLASS",
                                  "TYPE","X","Y","NPRN","COMMUNITY","NGR","OLDCOUNTY","hbsmr_id","ar_or_ev","visible",
                                  "east","nrth","dataorigin","changedata","shine_stat","rowid","compiler","compileod"
                                  "compilero","lastupdate","lastupdate_1"])

    # Hide other attributes that cannot be deleted - NEED TO FIX!!!!!!!
    desiredFields = ['MonUID', 'EVUID' 'RecordType', 'PrefRef', 'Name', 'PeriodRang', 'Period', 'Easting', 'Northing',
                     'PeriodFrom']
    field_info = arcpy.Describe(featureClass).fieldInfo
    for i in range(field_info.count):
        if field_info.getfieldname(i) not in desiredFields:
            field_info.setvisible(i, 'HIDDEN')

    # if PeriodFrom is required then the dictionary will classify the new column with new values
    arcpy.SetProgressorLabel("Calculating PeriodFrom Values")

    fields = [fcColumn, 'periodFrom']
    # Dictionary of old and new value. Add all your values here, instead of many if/elifs
    remap = {
        'Palaeolithic': 'Palaeolithic',
	'Palaeolithic to Roman':'Palaeolithic',
        'PALAEOLITHIC':'Palaeolithic',
        'Palaeolithic to Bronze Age':'Prehistoric',
	'Lower Palaeolithic': 'Palaeolithic',
        'Lower Palaeolithic to Middle Palaeolithic': 'Palaeolithic',
        'Middle Palaeolithic': 'Palaeolithic',
        'Upper Palaeolothic': 'Palaeoalithic',
        'Later Prehistoric': 'Prehistoric',
        'Prehistoric': 'Prehistoric',
        'PREHISTORIC': 'Prehistoric',
        'PREHISTORIC;MEDIEVAL': 'User Input needed',
        'Late Prehistoric': 'Prehistoric',
        'Mesolithic': 'Mesolithic',
        'MESOLITHIC': 'Mesolithic',
        'Early Mesolithic to Early Neolithic': 'Prehistoric',
        'Late Mesolithic to Late Bronze Age': 'Mesolithic',
        'Mesolithic to Bronze Age':'Prehistoric',
	'Mesolithic to Neolithic':'Prehistoric',
        'Neolithic': 'Neolithic',
        'NEOLITHIC': 'Neolithic',
        'NEOLITHIC;BRONZE AGE': 'Prehistoric',
	'Neolithic to Iron Age':'Prehistoric',
	'Neolithic to Roman':'Prehistoric',
        'Early Neolithic': 'Neolithic',
        'Early Neolithic to Late Bronze Age': 'Neolithic',
        'Early Neolithic to Post Medieval': 'User Input needed',
        'Neolithic to Late Bronze Age': 'Prehistoric',
	'Neolithic to Bronze Age':'Prehistoric',
        'Late Neolithic to Early Bronze Age': 'Neolithic',
        'Late Neolithic to Late Bronze Age':'Neolithic',
	'Bronze Age to Iron Age':'Prehistoric',
        'Bronze Age': 'Bronze Age',
        'BRONZE AGE': 'Bronze Age',
        'BRONZE AGE;MESOLITHIC': 'User input needed',
        'Early Bronze Age to Middle Bronze Age':'Bronze',
        'Early Bronze Age': 'Bronze Age',
        'Early Bronze Age to Middle Iron Age': 'Bronze Age',
        'Early Bronze Age to Roman': 'Bronze Age',
        'Middle Bronze Age': 'Bronze Age',
        'Middle Bronze Age to Early Iron Age': 'Bronze Age',
        'Middle Bronze Age to Middle Iron Age': 'Bronze Age',
        'Middle Bronze Age to Late Bronze Age': 'Bronze Age',
        'Late Bronze Age': 'Bronze Age',
        'Late Bronze Age to Early Iron Age': 'Bronze Age',
        'Late Bronze Age to Late Iron Age': 'Bronze Age',
        'Iron Age': 'Iron Age',
        'IRON AGE': 'Iron Age',
	'Iron Age to Early Medieval':'User Input needed',
        'Early Iron Age to Roman': 'Iron Age',
        'Early Iron Age': 'Iron Age',
        'Early Iron Age to Middle Iron Age': 'Iron Age',
        'Early Iron Age to Early Medieval or Anglo-Saxon': 'User Input needed',
        'Middle Iron Age to Late Iron Age': 'Iron Age',
        'Middle Iron Age': 'Iron Age',
        'Middle Iron Age to Roman': 'User Input needed',
        'Late Iron Age': 'Iron Age',
        'Late Iron Age to Roman': 'Iron Age',
        'Late Iron Age to Medieval': 'User Input needed',
        'Early Iron Age to Early Medieval':'User Input needed',
        'Iron Age to Roman':'Iron Age',
	'Roman': 'Romano-British',
        'ROMAN': 'Romano-British',
        'Roman to Georgian': 'Romano-British',
        'Roman to Unknown': 'Romano-British',
        'Romano-British': 'Romano-British',
        'Roman to Early Medieval or Anglo-Saxon': 'User Input needed',
        'Roman to Medieval': 'Romano-British',
        'Early Medieval': 'Anglo-Saxon',
        'Anglo-Saxon': 'Anglo-Saxon',
        'ANGLO-SAXON': 'Anglo-Saxon',
        'Early Medieval or Anglo-Saxon to Medieval': 'Anglo-Saxon',
        'Early Medieval or Anglo-Saxon': 'Anglo-Saxon',
        'Saxon': 'Anglo-Saxon',
        'Anglo Saxon': 'Anglo-Saxon',
        'Early Medieval/Dark Age': 'Anglo-Saxon',
	'Early Medieval to Post Medieval':'Medieval',
        'EARLY MEDIEVAL': 'Anglo-Saxon',
        'EARLY MEDIEVAL;MEDIEVAL': 'Anglo-Saxon',
        'Early Medieval to Medieval':'Anglo-Saxon',
        'Medieval to Post-Medieval':'Medieval',
        'Medieval': 'Medieval',
        'MEDIEVAL': 'Medieval',
	'Medieval to Unknown':'Medieval',
        'Medieval to Late C19': 'Medieval',
        'Medieval to Modern': 'Medieval',
        'MEDIEVAL;POST MEDIEVAL': 'Medieval',
        'Late Medieval': 'Medieval',
        'Medieval to Post Medieval': 'Medieval',
        'Medieval to Early 20th Century':'Medieval',
        'Post Medieval to C20':'Post-medieval',
        '15th Century to 19th Century':'Medieval',
        'Post Medieval to Late C17':'Post-medieval',
        'Stuart': 'Post-medieval',
        'POST MEDIEVAL': 'Post-medieval',
        'POST MEDIEVAL;MEDIEVAL': 'Post-medieval',
        'POST MEDIEVAL;PREHISTORIC': 'Post-medieval',
        'POST MEDIEVAL;ROMAN': 'Post-medieval',
        'Post-medieval': 'Post-medieval',
        'Post Medieval to Modern': 'Post-medieval',
        'Post Medieval': 'Post-medieval',
        'Post medieval': 'Post-medieval',
        'Post Medieval to Unknown': 'Post-medieval',
        'Early C18 to Late C19': 'Post-medieval',
        'Early C18 to C20': 'Post-medieval',
        'Late C17 to Late C18': 'Post-medieval',
        'C17': 'Post-medieval',
        '17th Century':'Post-medieval',
        '16TH CENTURY':'Post-medieval',
        '18TH CENTURY':'Post-medieval',
        '18th Century to Modern':'Post-medieval',
        'Post Medieval to Late 20th Century': 'Post-medieval',
        'Post Medieval to Mid 20th Century': 'Post-medieval',
        'Post Medieval to Early 20th Century': 'Post-medieval',
        '19th Century, Post Mediev':'Post-medieval',
        'Late C18 to Late C19':'19th century',
        'Late C18 to Early C19':'post-medieval',
        'Mid C19 to Late C19':'19th century',
        'Victorian': '19th century',
        'Victorian to Early 20th Century':'19th century',
        'Victorian to Second World War':'19th century',
        'Georgian to Modern': '19th century',
        'Georgian to Victorian':'19th century',
        'Georgian to Early 20th Century':'19th century',
        '19TH CENTURY':'19th century',
        '19th century': '19th century',
        'Hanoverian': '19th century',
        'Stuart to Georgian':'Post-medieval',
        'C19': '19th century',
        'Mid C19': '19th century',
        'Victorian to Mid 20th Century': '19th century',
        '19th Century to 21st Century':'19th century',
        '19th Century to Modern':'19th century',
        'Modern': 'Modern',
        '20th Century, Modern':'Modern',
        'Edwardian': 'Modern',
        'MODERN': 'Modern',
	'Modern to Unknown':'Modern',
        'modern': 'Modern',
        'C20': 'Modern',
        'Early 20th Century to 21st Century':'Modern',
        'Second World War': 'Modern',
        'second world war': 'Modern',
        'World War II':'Modern',
        'World War Two to Modern':'Modern',
        'WWII': 'Modern',
        'World War I':'Modern',
        'World War One to Modern':'Modern',
	'World War One': 'Modern',
        'world war one': 'Modern',
        'WWI': 'Modern',
        '20th Century': 'Modern',
        '20TH CENTURY':'Modern',
        'Unknown': 'Undated',
        'Unknown to Modern': 'Undated',
        'UNKNOWN': 'Unknown',
        ' ': 'User Input needed',
        'MULTIPERIOD': 'Multi-period',
        'Multiperiod':'Multi-period',
        'Undated': 'Undated'
    }
    if fcColumn == 'not required':
        arcpy.AddMessage("re-classification not required")
    else:
        with arcpy.da.UpdateCursor(featureClass, fields) as cursor:
            for row in cursor:
                row[0] in remap
                row[1] = remap[row[0]]
                cursor.updateRow(row)
    arcpy.AddMessage("PeriodFrom Classified")
    # replace the symbology with existing feature layers
    if symbology == "Lines":
        arcpy.ApplySymbologyFromLayer_management(featureClass, "K:/GIS/_WAGIS_Styles/LYR/HER_periods_lines.lyr")
    elif symbology == "Points":
        arcpy.ApplySymbologyFromLayer_management(featureClass, "K:/GIS/_WAGIS_Styles/LYR/HER_periods _points.lyr")
    else:
        arcpy.ApplySymbologyFromLayer_management(featureClass, "K:/GIS/_WAGIS_Styles/LYR/HER_periods_polygons.lyr")
    arcpy.AddMessage("Symbology Applied")
    arcpy.GetMessages()
except Exception as e:
    arcpy.AddError(e)
