import requests
from urllib.parse import urljoin

from django.conf import settings

from rest_framework import status, views
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.users.authentication import ProxyAuthentication
from safers.users.permissions import IsRemote


class DataLayerMetadataView(views.APIView):

    permission_classes = [IsAuthenticated, IsRemote]

    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: openapi.Schema(type=openapi.TYPE_STRING)
        }
    )
    def get(self, request, *args, **kwargs):
        """
        get metadata for a specific data layer
        """

        GATEWAY_URL_PATH = "/api/services/app/Layers/GetMetadata"

        try:
            response = requests.get(
                urljoin(settings.SAFERS_GATEWAY_API_URL, GATEWAY_URL_PATH),
                auth=ProxyAuthentication(request.user),
                params={"MetadataId": self.kwargs["metadata_id"]},
            )
            response.raise_for_status()
        except Exception as e:
            raise APIException(e)

        metadata = response.json()

        return Response(data=metadata, status=status.HTTP_200_OK)


"""
SAMPLE PROXY DATA SHAPE:
{
  'author': 'fmi',
  'author_email': 'fmi',
  'classification_TopicCategory': 'climatologyMeteorologyAtmosphere',
  'conformity_degree': 'true',
  'conformity_specification_date': '2010-12-08T00:00:00',
  'conformity_specification_dateType': 'publication',
  'conformity_specification_title': 'COMMISSION REGULATION (EU) No 1089/2010 of 23 November 2010 implementing Directive 2007/2/EC of the European Parliament and of the Council as regards interoperability of spatial data sets and services',
  'constraints_conditions_for_access_and_use': 'License not specified',
  'constraints_limitation_on_public_access': '',
  'coordinatesystemreference_code': '4326',
  'coordinatesystemreference_codespace': 'EPSG',
  'creator_user_id': '9d6aaac5-3dd1-40a6-bbaa-4d2794b3288d',
  'data_temporal_extent_begin_date': '2022-05-13T01:00:00',
  'data_temporal_extent_end_date': '2022-05-16T00:00:00',
  'datatype_id': '33001',
  'external_attributes': {
    '__comment': 'These fields describe the forecast variable and forecast times.',
    'variables': [
      't2m',
      'r2',
      'd2m',
      'u10',
      'v10',
      'tp',
      'cape'
    ],
    'format': 'netCDF',
    'origintime': '2022-05-13T00:00:00',
    'name': '33001_FMI_EC_HRES_20220513T0000Z_20220513T0100Z_20220516T0000Z_EN.nc'
  },
  'id': '9a97ae85-7abf-4a5a-9327-4dd5af61134f',
  'identification_CoupledResource': '',
  'identification_ResourceLanguage': 'eng',
  'identification_ResourceType': 'service',
  'isopen': False,
  'keyword_KeywordValue': 'Meteorological Geographical Features',
  'keyword_OriginatingControlledVocabulary': 'ontology',
  'license_id': 'License not specified',
  'license_title': 'License not specified',
  'maintainer': None,
  'maintainer_email': None,
  'metadata_created': '2022-05-13T07:10:28.69016',
  'metadata_language': 'eng',
  'metadata_modified': '2022-05-13T07:11:37.248933',
  'name': 'd0153f16-0fe4-4dc4-b9ea-17c0e53bcc00',
  'notes': 'Deterministic high resolution forecast from ECMWF processed at FMI for several variables.',
  'num_resources': 1,
  'num_tags': 1,
  'organization': {
    'id': '5a610458-10f6-41b8-88c8-4d4bd3c66df4',
    'name': 'safers',
    'title': 'SAFERS',
    'type': 'organization',
    'description': 'In order to support societies becoming more resilient when acting against forests fires, the Horizon 2020-funded project SAFERS ‘Structured Approaches for Forest Fire Emergencies in Resilient Societies’ is going to create an open and integrated platform featuring a forest fire Decision Support System. The platform will use information from different sources: earth observations from Copernicus and GEOSS, fire sensors in forests, topographic data, weather forecasts and even crowdsourced data from social media and other apps that can be used by citizens and first responders to provide situational in-field information.',
    'image_url': 'https://safers-project.eu/images/logo-footer.png',
    'created': '2021-08-30T13:35:03.99431',
    'is_organization': True,
    'approval_status': 'approved',
    'state': 'active'
  },
  'owner_org': '5a610458-10f6-41b8-88c8-4d4bd3c66df4',
  'point_of_contact_email': 'marko.laine@fmi.fi',
  'point_of_contact_name': 'Marko Laine',
  'private': True,
  'quality_and_validity_lineage': 'Quality approved',
  'quality_and_validity_spatial_resolution_latitude': '0',
  'quality_and_validity_spatial_resolution_longitude': '0',
  'quality_and_validity_spatial_resolution_measureunit': 'm',
  'quality_and_validity_spatial_resolution_scale': '1',
  'responsable_organization_email': 'marko.laine@fmi.fi',
  'responsable_organization_name': 'Finnish Meteorological Institute',
  'responsable_organization_role': 'author',
  'spatial': '{"type": "MultiPolygon", "coordinates": [[[[-25.0, 25.499999999999908], [40.000000000000384, 25.499999999999908], [40.000000000000384, 72.0], [-25.0, 72.0], [-25.0, 25.499999999999908]]]]}',
  'state': 'active',
  'temporalReference_date': '2022-05-13T07:10:27',
  'temporalReference_dateOfCreation': '2022-05-13T07:10:27',
  'temporalReference_dateOfLastRevision': '2022-05-13T07:10:27',
  'temporalReference_dateOfPublication': '2022-05-13T07:10:27',
  'title': 'Deterministic forecasts for between 2022-05-13T01:00:00 and 2022-05-16T00:00:00',
  'type': 'dataset',
  'url': None,
  'version': None,
  'resources': [
    {
      'cache_last_updated': None,
      'cache_url': None,
      'created': '2022-05-13T07:11:25.067403',
      'datatype_resource': '33001',
      'description': None,
      'file_date_end': '2022-05-16T00:00:00',
      'file_date_start': '2022-05-13T01:00:00',
      'format': 'NetCDF',
      'hash': '',
      'id': '3389832d-860d-4367-b468-c852d620a1e0',
      'last_modified': None,
      'metadata_modified': '2022-05-13T07:11:25.06045',
      'mimetype': None,
      'mimetype_inner': None,
      'name': '33001_FMI_EC_HRES_20220513T0000Z_20220513T0100Z_20220516T0000Z_EN.nc',
      'origintime': '2022-05-13T00:00:00',
      'package_id': '9a97ae85-7abf-4a5a-9327-4dd5af61134f',
      'position': 0,
      'resource_type': None,
      'size': None,
      'state': 'active',
      'url': 'https://datalake-test.safers-project.cloud/dataset/9a97ae85-7abf-4a5a-9327-4dd5af61134f/resource/3389832d-860d-4367-b468-c852d620a1e0/download/fc202205130000_hres.nc',
      'url_type': 'upload'
    }
  ],
  'tags': [
    {
      'display_name': 'Meteorological Geographical Features',
      'id': '2e186362-54be-41e4-89fd-185b22c00ff2',
      'name': 'Meteorological Geographical Features',
      'state': 'active',
      'vocabulary_id': None
    }
  ],
  'groups': [
    
  ],
  'relationships_as_subject': [
    
  ],
  'relationships_as_object': [
    
  ]
}
"""
