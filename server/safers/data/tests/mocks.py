"""
mock data to use during development/testing
"""

MOCK_OPERATIONAL_LAYERS_DATA = {
    "layerGroups": [{
        "groupKey":
            "weather forecast",
        "group":
            "Weather forecast",
        "subGroups": [{
            "subGroupKey":
                "short term",
            "subGroup":
                "Short term",
            "layers":
                [{
                    "dataTypeId":
                        33101,
                    "group":
                        "Weather forecast",
                    "groupKey":
                        "weather forecast",
                    "subGroup":
                        "Short term",
                    "subGroupKey":
                        "short term",
                    "name":
                        "Temperature at 2m",
                    "partnerName":
                        "FMI",
                    "type":
                        "Forecast",
                    "frequency":
                        "H6",
                    "details": [{
                        "name":
                            "ermes:33101_t2m_33001_78a8a797-fb5c-4b40-9f12-88a64fffc616",
                        "timestamps": [
                            "2022-04-05T01:00:00Z",
                            "2022-04-05T02:00:00Z",
                        ],
                        "created_At":
                            "2022-04-05T07:10:30Z",
                        "request_Code":
                            None,
                        "mapRequestCode":
                            None,
                        "creator":
                            None
                    }]
                },
                 {
                     "dataTypeId":
                         35007,
                     "group":
                         "Environment",
                     "groupKey":
                         "environment",
                     "subGroup":
                         "Forecast",
                     "subGroupKey":
                         "forecast",
                     "name":
                         "Fire perimeter simulation as isochrones maps",
                     "partnerName":
                         "CIMA",
                     "type":
                         "Forecast",
                     "frequency":
                         "OnDemand",
                     "details": [{
                         "name":
                             "ermes:35007_85f6e495-c258-437d-a447-190742071807",
                         "timestamps": ["2021-12-12T16:00:00"],
                         "created_At":
                             "2022-03-10T12:14:43Z",
                         "request_Code":
                             None,
                         "mapRequestCode":
                             None,
                         "creator":
                             None
                     }]
                 },
                 {
                     "dataTypeId":
                         35008,
                     "group":
                         "Environment",
                     "groupKey":
                         "environment",
                     "subGroup":
                         "Forecast",
                     "subGroupKey":
                         "forecast",
                     "name":
                         "Mean fireline intensity",
                     "partnerName":
                         "CIMA",
                     "type":
                         "Forecast",
                     "frequency":
                         "OnDemand",
                     "details": [{
                         "name":
                             "ermes:35008_efc92e30-3333-408e-83bb-fcc43f6b3280",
                         "timestamps": ["2021-12-12T16:00:00"],
                         "created_At":
                             "2022-03-10T12:14:47Z",
                         "request_Code":
                             None,
                         "mapRequestCode":
                             None,
                         "creator":
                             None
                     }]
                 },
                 {
                     "dataTypeId":
                         35009,
                     "group":
                         "Environment",
                     "groupKey":
                         "environment",
                     "subGroup":
                         "Forecast",
                     "subGroupKey":
                         "forecast",
                     "name":
                         "Max fireline intensity",
                     "partnerName":
                         "CIMA",
                     "type":
                         "Forecast",
                     "frequency":
                         "OnDemand",
                     "details": [{
                         "name":
                             "ermes:35009_67576ad9-95c8-4736-9f28-cf4c13bc11bd",
                         "timestamps": ["2021-12-12T16:00:00"],
                         "created_At":
                             "2022-03-10T12:14:49Z",
                         "request_Code":
                             None,
                         "mapRequestCode":
                             None,
                         "creator":
                             None
                     }]
                 },
                 {
                     "dataTypeId":
                         35010,
                     "group":
                         "Environment",
                     "groupKey":
                         "environment",
                     "subGroup":
                         "Forecast",
                     "subGroupKey":
                         "forecast",
                     "name":
                         "Mean rate of spread",
                     "partnerName":
                         "CIMA",
                     "type":
                         "Forecast",
                     "frequency":
                         "OnDemand",
                     "details": [{
                         "name":
                             "ermes:35010_ae63de06-9161-4f9e-bcb1-1e1ebb215688",
                         "timestamps": ["2021-12-12T16:00:00"],
                         "created_At":
                             "2022-03-10T12:14:44Z",
                         "request_Code":
                             None,
                         "mapRequestCode":
                             None,
                         "creator":
                             None
                     }]
                 },
                 {
                     "dataTypeId":
                         35011,
                     "group":
                         "Environment",
                     "groupKey":
                         "environment",
                     "subGroup":
                         "Forecast",
                     "subGroupKey":
                         "forecast",
                     "name":
                         "Max rate of spread",
                     "partnerName":
                         "CIMA",
                     "type":
                         "Forecast",
                     "frequency":
                         "OnDemand",
                     "details": [{
                         "name":
                             "ermes:35011_42dcea6e-d4cd-4ba0-be9f-e79d576c6f82",
                         "timestamps": ["2021-12-12T16:00:00"],
                         "created_At":
                             "2022-03-10T12:14:46Z",
                         "request_Code":
                             None,
                         "mapRequestCode":
                             None,
                         "creator":
                             None
                     }]
                 }]
        }]
    }]
}  # yapf: disable