import clr
import sys

#Import libraries for Rhino
sys.path.append(r'C:\Program Files (x86)\Rhinoceros 5\System')
clr.AddReference("RhinoCommon")
import Rhino as rc

# Import libraries for Design Script
sys.path.append(r"C:\Program Files\Dynamo 0.9")
clr.AddReference('ProtoGeometry')
import Autodesk.DesignScript as ds

rc.Geometry.Point3d(1, 2, 0)

ds.Geometry.Point.ByCoordinates(1, 10)
