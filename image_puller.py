#!/usr/bin/env python3

import argparse

import os
import datetime

import json

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

import json
from shapely import geometry




parser = argparse.ArgumentParser(description='Create aerial images from a geometry file')
parser.add_argument('-g','--geometry-file', type=str, dest="geometryFile", required=True, help='geometry input file')
parser.add_argument('-a','--aerial-source', type=str, default="aerial.xml", required=False, dest="aerialFile", help='geometry input file')
parser.add_argument('-b','--buffer', type=int, default=400, required=True, dest="buffer", help='meters to buffer')
parser.add_argument('-r','--redo', type=int, dest="redo", help="individual index to redo")

def processClip(clipPoly, n):

    sequence = f'{n:03}'

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3857)
    
    geojsonDriver = ogr.GetDriverByName('GeoJSON')
    clipPolySrc = geojsonDriver.CreateDataSource("/vsimem/clip-{}.geojson".format(sequence))
    clipPolyLayer = clipPolySrc.CreateLayer("clip", srs, ogr.wkbPolygon)
    clipPolyProc = ogr.CreateGeometryFromJson(json.dumps(clipPoly))
    

    featureDfn = clipPolyLayer.GetLayerDefn()
    outFeature = ogr.Feature(featureDfn)
    outFeature.SetGeometry(clipPolyProc)

    clipPolyLayer.CreateFeature(outFeature)
    clipPolySrc = None


    
    options = gdal.WarpOptions(
        format='PNG',
        width=600,
        height=0,
        cutlineDSName='/vsimem/clip-{}.geojson'.format(sequence),
        cropToCutline=True
    )
    
    wmsSource = gdal.Open(args.aerialFile)


    try:
        w = gdal.Warp("./{}/{}.png".format(outDir, sequence), wmsSource, options=options)
        return True
    except:
        return False

def createImageClips(inputJson, buffer, outDir):

    for i,f in enumerate(inputJson['features']):

        if not args.redo or args.redo == i+1:

            shape = geometry.shape(f['geometry'])
            
            bounds = shape.bounds
            
            xDist = bounds[2] - bounds[0]
            yDist = bounds[3] - bounds[1]

            if(xDist > yDist):
                pad = (xDist - yDist)/2
                squareBoxCoords = (bounds[0]-buffer, bounds[1]-pad-buffer, bounds[2]+buffer, bounds[3]+pad+buffer)
                squareBox = geometry.box(*squareBoxCoords)
            else:
                pad = (yDist - xDist)/2
                squareBoxCoords = (bounds[0]-buffer-pad, bounds[1]-buffer, bounds[2]+pad+buffer, bounds[3]+buffer)
                squareBox = geometry.box(*squareBoxCoords)
            
            print(i+1)

            pc = processClip( geometry.mapping(squareBox), i+1 )


if __name__ == "__main__":
    try:
        args = parser.parse_args()

        with open(args.geometryFile,"r") as inputFile:
            inputJson = json.load(inputFile)
            
            outDir = f'{args.geometryFile} {datetime.datetime.now()}'
            os.mkdir(outDir)

            createImageClips(inputJson, args.buffer, outDir)

    except:
        print("Couldn't open geometry file")
        exit()