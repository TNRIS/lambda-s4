import os
import arcpy

dir = arcpy.GetParameterAsText(0)

for file in os.listdir(dir):
    file_path = os.path.join(dir, file)
    try:
        if os.path.isfile(file_path):
            sfx = file_path[-4:]
            arcpy.AddMessage(file_path)
            arcpy.AddMessage(sfx)
            if sfx != ".tif" and sfx != ".TIF":
                arcpy.AddMessage("deleting: " + file_path)
                os.remove(file_path)

    except Exception as e:
        print(e)
