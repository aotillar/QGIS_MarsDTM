"""
Model exported as python.
Name : MarsDEM_to_Contours
Group : 
With QGIS : 33414
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterCrs
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorDestination
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Marsdem_to_contours(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterNumber('contour_interval_5m', 'Contour_Interval_5m', type=QgsProcessingParameterNumber.Double, defaultValue=None))
        self.addParameter(QgsProcessingParameterCrs('mars_crs', 'Mars_CRS', defaultValue='IAU_2015:49910'))
        self.addParameter(QgsProcessingParameterRasterLayer('mars_dem', 'Mars_DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination('Countour_from_dem_5m', 'Countour_from_DEM_5m', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=''))
        self.addParameter(QgsProcessingParameterRasterDestination('Reprojected', 'Reprojected', createByDefault=True, defaultValue=''))
        self.addParameter(QgsProcessingParameterFeatureSink('Contour_lines_5m', 'Contour_Lines_5m', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}

        # Warp (reproject)
        alg_params = {
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': parameters['mars_dem'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,  # Nearest Neighbour
            'SOURCE_CRS': None,
            'TARGET_CRS': parameters['mars_crs'],
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': parameters['Reprojected']
        }
        outputs['WarpReproject'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Reprojected'] = outputs['WarpReproject']['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Contour Polygons
        alg_params = {
            'BAND': 1,
            'CREATE_3D': False,
            'EXTRA': '',
            'FIELD_NAME_MAX': 'ELEV_MAX',
            'FIELD_NAME_MIN': 'ELEV_MIN',
            'IGNORE_NODATA': False,
            'INPUT': outputs['WarpReproject']['OUTPUT'],
            'INTERVAL': parameters['contour_interval_5m'],
            'NODATA': None,
            'OFFSET': 0,
            'OUTPUT': parameters['Countour_from_dem_5m']
        }
        outputs['ContourPolygons'] = processing.run('gdal:contour_polygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Countour_from_dem_5m'] = outputs['ContourPolygons']['OUTPUT']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Contour
        alg_params = {
            'BAND': 1,
            'CREATE_3D': False,
            'EXTRA': '',
            'FIELD_NAME': 'ELEV',
            'IGNORE_NODATA': False,
            'INPUT': outputs['WarpReproject']['OUTPUT'],
            'INTERVAL': parameters['contour_interval_5m'],
            'NODATA': None,
            'OFFSET': 0,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Contour'] = processing.run('gdal:contour', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Smooth
        alg_params = {
            'INPUT': outputs['Contour']['OUTPUT'],
            'ITERATIONS': 4,
            'MAX_ANGLE': 90,
            'OFFSET': 0.5,
            'OUTPUT': parameters['Contour_lines_5m']
        }
        outputs['Smooth'] = processing.run('native:smoothgeometry', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Contour_lines_5m'] = outputs['Smooth']['OUTPUT']

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Set layer style
        alg_params = {
            'INPUT': outputs['Smooth']['OUTPUT'],
            'STYLE': 'D:\\Aaron Otillar\\Documents\\GIS\\Styles\\ColorRamps\\Contour_10meterStyle.qml'
        }
        outputs['SetLayerStyle'] = processing.run('native:setlayerstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'MarsDEM_to_Contours'

    def displayName(self):
        return 'MarsDEM_to_Contours'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Marsdem_to_contours()
