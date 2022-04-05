# Script to add Easting, Northing, and Distance to Site Boundary and to populate them, also adds a WANo field but does not populate it

import arcpy

# User Input 1 - Shapefile to be calculated
featureClass = arcpy.GetParameterAsText(0)
#user Input 2 - PeriodFrom required?
periodFrom = arcpy.GetParameterAsText(1)
#user Input 3 - state whether periodFrom is required and what column to use (Period, PeriodRang, DateRang, not required)
fcColumn = arcpy.GetParameterAsText(2)
#user Input 4 - select which existing layer to use for the symbology (Points, Polygons, Lines)
symbology = arcpy.GetParameterAsText(3)

#location of the symbology layers

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

    #Delete fields from the HER shapefiles that are not required
    arcpy.DeleteField_management (featureClass, ["condition","status","status gra","status ref","unitary au","Community","eastings", "northings","map sheet","MI_PRINX","Ref", "Organisati","DispDate","FeatureDes","Representa", "QualityNot"
                                "MinFrom","MaxTo","MonType","CapturePro","CaptureSca", "SourcePrec", "Accuracy", "Height", "Validation", "BufferZone",
                                                 "MI_STYLE","Finds", "WhenCreate", "CreatedBy","WhenLastEd", "LastEdited","MI_STYLE", "XgGeometry","MinFrom", "MaxTo"])

    #Hide other attributes that cannot be deleted - NEED TO FIX!!!!!!!
    desiredFields = ['MonUID', 'EVUID' 'RecordType', 'PrefRef', 'Name','PeriodRang','Period','Easting','Northing','PeriodFrom']
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
        'Lower Palaeolithic': 'Palaeolithic',
        'Lower Palaeolithic to Middle Palaeolithic': 'Palaeolithic',
        'Middle Palaeolithic': 'Palaeolithic',
        'Upper Palaeolothic': 'Palaeoalithic',
        'Later Prehistoric': 'Prehistoric',
        'Prehistoric': 'Prehistoric',
        'PREHISTORIC': 'Prehistoric',
        'PREHISTORIC;MEDIEVAL':'User Input needed',
        'Mesolithic': 'Mesolithic',
        'MESOLITHIC':'Mesolithic',
        'Early Mesolithic to Early Neolithic': 'Prehistoric',
        'Late Mesolithic to Late Bronze Age': 'Mesolithic',
        'Neolithic': 'Neolithic',
        'NEOLITHIC':'Neolithic',
        'NEOLITHIC;BRONZE AGE':'Prehistoric',
        'Early Neolithic': 'Neolithic',
        'Early Neolithic to Late Bronze Age': 'Neolithic',
        'Early Neolithic to Post Medieval':'User Input needed',
        'Neolithic to Late Bronze Age': 'Prehistoric',
        'Late Neolithic to Early Bronze Age':'Neolithic',
        'Bronze Age': 'Bronze Age',
        'BRONZE AGE':'Bronze Age',
        'BRONZE AGE;MESOLITHIC':'User input needed',
        'Early Bronze Age': 'Bronze Age',
        'Early Bronze Age to Middle Iron Age': 'Bronze Age',
        'Early Bronze Age to Roman':'User Input needed',
        'Middle Bronze Age': 'Bronze Age',
        'Middle Bronze Age to Early Iron Age': 'Bronze Age',
        'Middle Bronze Age to Middle Iron Age':'Bronze Age',
        'Middle Bronze Age to Late Bronze Age':'Bronze Age',
        'Late Bronze Age': 'Bronze Age',
        'Late Bronze Age to Early Iron Age': 'Bronze Age',
        'Late Bronze Age to Late Iron Age':'Bronze Age',
        'Iron Age': 'Iron Age',
        'IRON AGE':'Iron Age',
        'Early Iron Age to Roman':'Iron Age',
        'Early Iron Age': 'Iron Age',
        'Early Iron Age to Middle Iron Age': 'Iron Age',
        'Early Iron Age to Early Medieval or Anglo-Saxon':'User Input needed',
        'Middle Iron Age to Late Iron Age': 'Iron Age',
        'Middle Iron Age': 'Iron Age',
        'Middle Iron Age to Roman':'User Input needed',
        'Late Iron Age': 'Iron Age',
        'Late Iron Age to Roman': 'Iron Age',
        'Late Iron Age to Medieval':'User Input needed',
        'Roman': 'Romano-British',
        'ROMAN':'Romano-British',
        'Roman to Unknown':'Romano-British',
        'Romano-British': 'Romano-British',
        'Roman to Early Medieval or Anglo-Saxon':'User Input needed',
        'Early Medieval': 'Anglo-Saxon',
        'Early Medieval to Medieval': 'Anglo-Saxon',
        'Anglo-Saxon': 'Anglo-Saxon',
        'ANGLO-SAXON':'Anglo-Saxon',
        'Early Medieval or Anglo-Saxon to Medieval': 'Anglo-Saxon',
        'Early Medieval or Anglo-Saxon':'Anglo-Saxon',
        'Saxon': 'Anglo-Saxon',
        'Anglo Saxon': 'Anglo-Saxon',
	    'Early Medieval/Dark Age':'Anglo-Saxon',
        'EARLY MEDIEVAL':'Anglo-Saxon',
        'EARLY MEDIEVAL;MEDIEVAL':'Anglo-Saxon',
        'Medieval': 'Medieval',
        'MEDIEVAL':'Medieval',
        'Medieval to Modern':'User Input needed',
        'MEDIEVAL;POST MEDIEVAL':'Medieval',
        'Late Medieval': 'Medieval',
        'Medieval to Post Medieval': 'Medieval',
        'POST MEDIEVAL':'Post-medieval',
        'POST MEDIEVAL;MEDIEVAL':'Post-medieval',
        'POST MEDIEVAL;PREHISTORIC':'Post-medieval',
        'POST MEDIEVAL;ROMAN':'Post-medieval',
        'Post-medieval': 'Post-medieval',
        'Post Medieval to Modern': 'Post-medieval',
        'Post Medieval': 'Post-medieval',
        'Post medieval': 'Post-medieval',
        'Post Medieval to Unknown':'Post-medieval',
        '19th century': '19th century',
        'Modern': 'Modern',
        'MODERN':'Modern',
        'modern': 'Modern',
        'Unknown': 'Undated',
        'Unknown to Modern':'Undated',
        'UNKNOWN':'Unknown',
	    ' ':'User Input needed',
        'MULTIPERIOD':'User Input needed',
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
    #replace the symbology with existing feature layers
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
