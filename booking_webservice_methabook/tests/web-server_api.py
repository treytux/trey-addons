# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from klein import Klein


class ItemStore(object):
    app = Klein()

    def __init__(self):
        zones = '''{
            "Export": {
                "ExportId": "06797bb4-43a2-4485-a009-eb9c06c0d4cd",
                "Track": "rrt-03fa84a43dbf41f39-b-eu-2423-7689603-2",
                "ExportedAt": "2017-08-24 11:28:46.902",
                "Customers": [
                ],
                "Suppliers": [
                ],
                "Zones": [
                    {
                        "Code": "000001",
                        "Name": "United Arab Emirates",
                        "ParentZone": null
                    },
                    {
                        "Code": "000002",
                        "Name": "Argentina",
                        "ParentZone": null
                    },
                    {
                        "Code": "000003",
                        "Name": "Spain",
                        "ParentZone": null
                    },
                    {
                        "Code": "000004",
                        "Name": "United Kingdom",
                        "ParentZone": null
                    },
                    {
                        "Code": "000005",
                        "Name": "Italy",
                        "ParentZone": null
                    },
                    {
                        "Code": "000006",
                        "Name": "Portugal",
                        "ParentZone": null
                    },
                    {
                        "Code": "000007",
                        "Name": "Almeria",
                        "ParentZone": "000003"
                    },
                    {
                        "Code": "000008",
                        "Name": "Cadiz",
                        "ParentZone": "000003"
                    },
                    {
                        "Code": "000009",
                        "Name": "Cordoba",
                        "ParentZone": "000003"
                    },
                    {
                        "Code": "000010",
                        "Name": "Granada",
                        "ParentZone": "000003"
                    },
                    {
                        "Code": "000011",
                        "Name": "Huelva",
                        "ParentZone": "000003"
                    },
                    {
                        "Code": "000012",
                        "Name": "Jaen",
                        "ParentZone": "000003"
                    },
                    {
                        "Code": "000013",
                        "Name": "Malaga",
                        "ParentZone": "000003"
                    },
                    {
                        "Code": "000014",
                        "Name": "Seville",
                        "ParentZone": "000003"
                    },
                    {
                        "Code": "000015",
                        "Name": "Huesca",
                        "ParentZone": "000003"
                    },
                    {
                        "Code": "000016",
                        "Name": "Teruel",
                        "ParentZone": "000003"
                    }
                ],
                "Bookings": [
                ]
            }
        }
        '''
        customers = ('''{
            "Export": {
                "ExportId": "06797bb4-43a2-4485-a009-eb9c06c0d4cd",
                "Track": "rrt-03fa84a43dbf41f39-b-eu-2423-7689603-2",
                "ExportedAt": "2017-08-24 11:28:46.902",
                "Customers": [
                    {
                        "Account": "430004476",
                        "Name": "HotelTravelAgent.net",
                        "LegalName": "HotelTravelAgent",
                        "Phone": "1-212-989-1386 / 866-397-1300",
                        "Email": "mfriedman@hoteltravelagent.net",
                        "Vat": "461639461",
                        "Location": {
                            "Address": "1472 47th Street, Brooklyn",
                            "City": "New York",
                            "Province": null,
                            "Country": "USA",
                            "PostalCode": "11219"
                        }
                    },
                    {
                        "Account": "430000483",
                        "Name": "Viagens Mark Operadora",
                        "LegalName":
                        "Viagens Mark Operadora de Turismo e Receptivo Eireli",
                        "Phone": "0055 85 3242-7353",
                        "Email": "aline@viagensmark.com.br",
                        "Vat": "16.584.066/0001-06",
                        "Location": {
                            "Address":
                            "Rua Pe. Carlos Quixada, 175 - Parangaba",
                            "City": "Fortaleza",
                            "Province": null,
                            "Country": "Brazil",
                            "PostalCode": "60740-540"
                        }
                    },
                    {
                        "Account": "430004480",
                        "Name": "Travel Experience",
                        "LegalName": "Travel Experience",
                        "Phone": "xxxxx",
                        "Email": "dave@travelexperience.be",
                        "Vat": "Be 0460.860.460",
                        "Location": {
                            "Address": "Astridplein 4",
                            "City": "Grobbendonk",
                            "Province": null,
                            "Country": "Belgium",
                            "PostalCode": "2280"
                        }
                    },
                    {
                        "Account": "430004482",
                        "Name": "Check In Viajes",
                        "LegalName": "Check In Viajes",
                        "Phone": "(33) 3616 7244",
                        "Email": "victor@checkinviajes.mx",
                        "Vat": "CVC140325UE0",
                        "Location": {
                            "Address":
                            "Av. Guadalupe 6340-6 - Centro Com. Plaza Cibeles",
                            "City": "Zapopan Jalisco",
                            "Province": null,
                            "Country": "Mexico",
                            "PostalCode": "45010"
                        }
                    },
                    {
                        "Account": "430000042",
                        "Name": "Explore the Wonders",
                        "LegalName": "Explore the Wonders",
                        "Phone": "+971 6 557 3938",
                        "Email": "desmond@etws.ae",
                        "Vat": "08496",
                        "Location": {
                            "Address":
                            "Sharjah Airport International Free Zone, Z2",
                            "City": "Sharjah",
                            "Province": null,
                            "Country": "UAE",
                            "PostalCode": "P.O.Box 120924"
                        }
                    },
                    {
                        "Account": "430000438",
                        "Name": "Almosafer B2B",
                        "LegalName": "Al Tayyar Travel Group",
                        "Phone": "+20101333304",
                        "Email": "ahmed.fouad@almosaferer.com",
                        "Vat": "1010148039",
                        "Location": {
                            "Address": "Ulaya, Riyadh KSA",
                            "City": "Rihad",
                            "Province": null,
                            "Country": "Arabia Saudi",
                            "PostalCode": "XXXX"
                        }
                    },
                    {
                        "Account": "430004479",
                        "Name": "Rocket Miles",
                        "LegalName": "Rocket Trave, Inc.",
                        "Phone": "0013308583659",
                        "Email": "john@rocketmiles.com",
                        "Vat": "RKM XXX",
                        "Location": {
                            "Address": "641 W, Lake Street",
                            "City": "Chicago",
                            "Province": null,
                            "Country": "USA",
                            "PostalCode": "IL 60661"
                        }
                    }
                ],
                "Suppliers": [
                ],
                "Zones": [
                ],
                "Bookings": [
                ]
            }
        }
        ''')
        suppliers = ('''{
            "Export": {
                "ExportId": "06797bb4-43a2-4485-a009-eb9c06c0d4cd",
                "Track": "rrt-03fa84a43dbf41f39-b-eu-2423-7689603-2",
                "ExportedAt": "2017-08-24 11:28:46.902",
                "Customers": [
                ],
                "Suppliers": [
                    {
                        "Account": "400000001",
                        "Name": "Hotelbeds Hotel",
                        "FiscalName": "Hotelbeds S.L.U.",
                        "Phone": "+34971178821",
                        "Email": "m.suero@hotelbeds.com",
                        "Vat": "B57218372",
                        "Location": {
                            "Address":
                            "Cami de Son Fangos Nº100 Torre A 5º planta",
                            "City": "Palma de Mallorca",
                            "Province": null,
                            "Country": "Spain",
                            "PostalCode": "07007"
                        }
                    },
                    {
                        "Account": "400000002",
                        "Name": "Hotelbeds USA",
                        "FiscalName": "HOTELBEDS USA INC.",
                        "Phone": "+34971178821",
                        "Email": "m.suero@hotelbeds.com",
                        "Vat": "592952685",
                        "Location": {
                            "Address": "5422 Carrier Drive, suite 201",
                            "City": "Orlando",
                            "Province": null,
                            "Country": "USA",
                            "PostalCode": "32819"
                        }
                    },
                    {
                        "Account": "400000011",
                        "Name": "Jac Travel",
                        "FiscalName": "JAC TRAVEL LTD",
                        "Phone": "+4402078708588",
                        "Email": "res@jactravel.co.uk",
                        "Vat": "4714729",
                        "Location": {
                            "Address": "62-64 Chancellors Road",
                            "City": "Hammersmith",
                            "Province": "London",
                            "Country": "United Kindong",
                            "PostalCode": "W6 9RS"
                        }
                    },
                    {
                        "Account": "400000010",
                        "Name": "Hoteldo",
                        "FiscalName": "JAMIRAY INTERNACIONAL S.A",
                        "Phone": "+541155528330",
                        "Email": "operaciones.es@hoteldo.com",
                        "Vat": "RUT 216572900014",
                        "Location": {
                            "Address":
                            "Ruta 8 Km 17500 Edificio 200 of. 205A Zonamerica",
                            "City": "Montevideo",
                            "Province": null,
                            "Country": "Urugay",
                            "PostalCode": "17500"
                        }
                    },
                    {
                        "Account": "400000021",
                        "Name": "Teamamerica",
                        "FiscalName": "TEAMAMERICA INC",
                        "Phone": "+12126977165",
                        "Email": "fit@teamamericany.com",
                        "Vat": "13-3980339",
                        "Location": {
                            "Address": "33 West 46th Street-Third FL",
                            "City": "New York",
                            "Province": "New York",
                            "Country": "USA",
                            "PostalCode": "10036"
                        }
                    },
                    {
                        "Account": "400000024",
                        "Name": "Travco",
                        "FiscalName": "Travco Corporation Ltd",
                        "Phone": "+442078646129",
                        "Email": "fit.res@travco.co.uk",
                        "Vat": "9276634",
                        "Location": {
                            "Address": "92-94 Paul Street",
                            "City": "London",
                            "Province": null,
                            "Country": "United Kindong",
                            "PostalCode": "EC2A 4UX"
                        }
                    },
                    {
                        "Account": "400000014",
                        "Name": "GTA",
                        "FiscalName": "Kuoni Global Travel Services AG",
                        "Phone": "+34915226101",
                        "Email": "technical.support@gta-travel.com",
                        "Vat": "CHE-425.060.629",
                        "Location": {
                            "Address": "Überlandstrasse 360",
                            "City": "Zurich",
                            "Province": "",
                            "Country": "Suiza",
                            "PostalCode": "8051"
                        }
                    }
                ],
                "Zones": [
                ],
                "Bookings": [
                ]
            }
        }
        ''')
        bookings = ('''{
            "Export": {
                "ExportId": "06797bb4-43a2-4485-a009-eb9c06c0d4cd",
                "Track": "rrt-03fa84a43dbf41f39-b-eu-2423-7689603-2",
                "ExportedAt": "2017-08-24 11:28:46.902",
                "Customers": [
                ],
                "Suppliers": [
                ],
                "Zones": [
                ],
                "Bookings": [
                    {
                        "Locator": "3B7U2739",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "ahmad",
                            "Surname": "almalik"
                        },
                        "CreationDate": "2017-08-28T12:17:35.079Z",
                        "ModificationDate": "2017-08-28T12:17:35.079Z",
                        "ExpirationDate": "2017-08-28T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "148-930156",
                                    "Status": "Confirmed",
                                    "Description": "Dusit Thani Dubai",
                                    "CheckInDate": "2017-08-30T00:00:00Z",
                                    "CheckOutDate": "2017-09-06T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 2893.41,
                                            "Net": 2748.74,
                                            "Commission": 144.67,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 2783.53,
                                            "Net": 2783.53,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 2748.74,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 2783.53,
                                            "Net": 2783.53,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "3FTJKBUR",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Hammouda",
                            "Surname": "Raida"
                        },
                        "CreationDate": "2017-08-28T12:22:42.13Z",
                        "ModificationDate": "2017-08-28T12:22:42.13Z",
                        "ExpirationDate": "2017-08-30T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291099471_141070727355",
                                    "Status": "Confirmed",
                                    "Description": "Nassima Royal Hotel",
                                    "CheckInDate": "2017-08-31T00:00:00Z",
                                    "CheckOutDate": "2017-09-03T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 276.9,
                                            "Net": 276.9,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 269.49,
                                            "Net": 269.49,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 276.9,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 269.49,
                                            "Net": 269.49,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        ''')
        complete_no_zones = ('''{
            "Export": {
                "ExportId": "202bde2c-b35e-4e18-8a8e-92f4bbe71f3d",
                "Track": "rrt-0ecb05c66906b353e-a-eu-19045-17256595-1",
                "ExportedAt": "2017-08-31 07:30:16.305",
                "Customers": [
                    {
                        "Account": "430000392",
                        "Name": "Ostrovok B2B",
                        "LegalName": "Emerging Travel",
                        "Phone": "+74992156525",
                        "Email": "res@ostrovok.ru",
                        "Vat": "XXX",
                        "Location": {
                            "Address": "3500 S. DuPont Hwy",
                            "City": "Dover (Delaware)",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "19901"
                        }
                    },
                    {
                        "Account": "430004478",
                        "Name": "Nustay",
                        "LegalName": "Nustay",
                        "Phone": "+45 31 18 89 89",
                        "Email": "dc@nustay.com",
                        "Vat": "36090316",
                        "Location": {
                            "Address": "test",
                            "City": "test",
                            "Province": null,
                            "Country": "DK",
                            "PostalCode": "test"
                        }
                    },
                    {
                        "Account": "430004476",
                        "Name": "HotelTravelAgent.net",
                        "LegalName": "HotelTravelAgent",
                        "Phone": "1-212-989-1386 / 866-397-1300",
                        "Email": "mfriedman@hoteltravelagent.net",
                        "Vat": "461639461",
                        "Location": {
                            "Address": "1472 47th Street, Brooklyn",
                            "City": "New York",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "11219"
                        }
                    },
                    {
                        "Account": "430000450",
                        "Name": "Tektraveler International",
                        "LegalName": "Tektraveler International LLC",
                        "Phone": "001 (281) 9078620",
                        "Email": "andre@tektraveler.com",
                        "Vat": "46-2774812",
                        "Location": {
                            "Address": "The Woodlands, TX",
                            "City": "Houston",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "77380"
                        }
                    },
                    {
                        "Account": "430004477",
                        "Name": "IBC Hotels",
                        "LegalName": "IBC Hospitality",
                        "Phone": "602-944-1500 ext. 215",
                        "Email": "pbarnhill@innsuites.com",
                        "Vat": "34-6647590",
                        "Location": {
                            "Address": "1625 E. Northern Ave 105",
                            "City": "Phoenix",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "85020"
                        }
                    },
                    {
                        "Account": "430004475",
                        "Name": "Hotelspro",
                        "LegalName": "Hotelspro DMCC",
                        "Phone": "05309552463",
                        "Email": "emre.senol@metglobal.com",
                        "Vat": "xxxxxx",
                        "Location": {
                            "Address":
                            "Saba Tower 1, Cluster E, Office 2602, Jumeirah",
                            "City": "Dubai",
                            "Province": null,
                            "Country": "AE",
                            "PostalCode": "336315"
                        }
                    },
                    {
                        "Account": "430004474",
                        "Name": "Haoqiao",
                        "LegalName":
                        "Beijing Haoqiao international Travel Agency Limited",
                        "Phone": "010-62016080",
                        "Email": "zhuweiyan@haoqiao.cn",
                        "Vat": "110106355274393",
                        "Location": {
                            "Address": "Room 611, F6, Changxin Mansion, 69",
                            "City": "Beijing",
                            "Province": null,
                            "Country": "CN",
                            "PostalCode": "xx"
                        }
                    },
                    {
                        "Account": "430000438",
                        "Name": "Almosafer B2B",
                        "LegalName": "Al Tayyar Travel Group",
                        "Phone": "+20101333304",
                        "Email": "ahmed.fouad@almosaferer.com",
                        "Vat": "1010148039",
                        "Location": {
                            "Address": "Ulaya, Riyadh KSA",
                            "City": "Rihad",
                            "Province": null,
                            "Country": "SA",
                            "PostalCode": "XXXX"
                        }
                    },
                    {
                        "Account": "430000299",
                        "Name": "Italcamel",
                        "LegalName": "Italcamel Travel Agency s.r.l.",
                        "Phone": "00390541661711",
                        "Email": "simona.gagliazzo@italcamel.com",
                        "Vat": "1227490404",
                        "Location": {
                            "Address": "viale Dante, 155",
                            "City": "Riccione",
                            "Province": null,
                            "Country": "IT",
                            "PostalCode": "00390541661711"
                        }
                    },
                    {
                        "Account": "430000483",
                        "Name": "Viagens Mark Operadora",
                        "LegalName":
                        "Viagens Mark Operadora de Turismo e Receptivo Eireli",
                        "Phone": "0055 85 3242-7353",
                        "Email": "aline@viagensmark.com.br",
                        "Vat": "16.584.066/0001-06",
                        "Location": {
                            "Address":
                            "Rua Pe. Carlos Quixada, 175 - Parangaba",
                            "City": "Fortaleza",
                            "Province": null,
                            "Country": "BR",
                            "PostalCode": "60740-540"
                        }
                    },
                    {
                        "Account": "430004480",
                        "Name": "Travel Experience",
                        "LegalName": "Travel Experience",
                        "Phone": "xxxxx",
                        "Email": "dave@travelexperience.be",
                        "Vat": "Be 0460.860.460",
                        "Location": {
                            "Address": "Astridplein 4",
                            "City": "Grobbendonk",
                            "Province": null,
                            "Country": "BE",
                            "PostalCode": "2280"
                        }
                    },
                    {
                        "Account": "430004473",
                        "Name": "Check In Viajes",
                        "LegalName": "Operadora de Viajes Check In SA de CV",
                        "Phone": "(33) 3616 7244",
                        "Email": "victor@checkinviajes.mx",
                        "Vat": "OVC140325UE0",
                        "Location": {
                            "Address":
                            "Av. Guadalupe 6340-6 - Centro Com. Plaza Cibeles",
                            "City": "Zapopan Jalisco",
                            "Province": null,
                            "Country": "MX",
                            "PostalCode": "45010"
                        }
                    },
                    {
                        "Account": "430000042",
                        "Name": "Explore the Wonders",
                        "LegalName": "Explore the Wonders",
                        "Phone": "+971 6 557 3938",
                        "Email": "desmond@etws.ae",
                        "Vat": "08496",
                        "Location": {
                            "Address": "Sharjah Airport International Free",
                            "City": "Sharjah",
                            "Province": null,
                            "Country": "AE",
                            "PostalCode": "P.O.Box 120924"
                        }
                    },
                    {
                        "Account": "430004479",
                        "Name": "Rocket Miles",
                        "LegalName": "Rocket Trave, Inc.",
                        "Phone": "0013308583659",
                        "Email": "john@rocketmiles.com",
                        "Vat": "461105421",
                        "Location": {
                            "Address": "641 W, Lake Street",
                            "City": "Chicago",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "IL 60661"
                        }
                    },
                    {
                        "Account": "430004481",
                        "Name": "eHotel AG",
                        "LegalName": "eHotel AG",
                        "Phone": "+49 30 47373 146",
                        "Email": "r.gegenfurtner@ehotel.de",
                        "Vat": "HRB78969",
                        "Location": {
                            "Address": "Greifswalder Str. 208",
                            "City": "Berlin",
                            "Province": null,
                            "Country": "DE",
                            "PostalCode": "10405"
                        }
                    }
                ],
                "Suppliers": [
                    {
                        "Account": "400000001",
                        "Name": "Hotelbeds Hotel",
                        "FiscalName": "Hotelbeds S.L.U.",
                        "Phone": "+34971178821",
                        "Email": "m.suero@hotelbeds.com",
                        "Vat": "B57218372",
                        "Location": {
                            "Address": "Cami de Son Fangos Nº100 Torre A 5º",
                            "City": "Palma de Mallorca",
                            "Province": null,
                            "Country": "ES",
                            "PostalCode": "07007"
                        }
                    },
                    {
                        "Account": "400000002",
                        "Name": "Hotelbeds USA",
                        "FiscalName": "HOTELBEDS USA INC.",
                        "Phone": "+34971178821",
                        "Email": "m.suero@hotelbeds.com",
                        "Vat": "592952685",
                        "Location": {
                            "Address": "5422 Carrier Drive, suite 201",
                            "City": "Orlando",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "32819"
                        }
                    },
                    {
                        "Account": "400000011",
                        "Name": "Jac Travel",
                        "FiscalName": "JAC TRAVEL LTD",
                        "Phone": "+4402078708588",
                        "Email": "res@jactravel.co.uk",
                        "Vat": "4714729",
                        "Location": {
                            "Address": "62-64 Chancellors Road",
                            "City": "Hammersmith",
                            "Province": "London",
                            "Country": "GB",
                            "PostalCode": "W6 9RS"
                        }
                    },
                    {
                        "Account": "400000010",
                        "Name": "Hoteldo",
                        "FiscalName": "JAMIRAY INTERNACIONAL S.A",
                        "Phone": "+541155528330",
                        "Email": "operaciones.es@hoteldo.com",
                        "Vat": "RUT 216572900014",
                        "Location": {
                            "Address": "Ruta 8 Km 17500 Edificio 200 of. 205A",
                            "City": "Montevideo",
                            "Province": null,
                            "Country": "UY",
                            "PostalCode": "17500"
                        }
                    },
                    {
                        "Account": "400000021",
                        "Name": "Teamamerica",
                        "FiscalName": "TEAMAMERICA INC",
                        "Phone": "+12126977165",
                        "Email": "fit@teamamericany.com",
                        "Vat": "13-3980339",
                        "Location": {
                            "Address": "33 West 46th Street-Third FL",
                            "City": "New York",
                            "Province": "New York",
                            "Country": "US",
                            "PostalCode": "10036"
                        }
                    },
                    {
                        "Account": "400000024",
                        "Name": "Travco",
                        "FiscalName": "Travco Corporation Ltd",
                        "Phone": "+442078646129",
                        "Email": "fit.res@travco.co.uk",
                        "Vat": "9276634",
                        "Location": {
                            "Address": "92-94 Paul Street",
                            "City": "London",
                            "Province": null,
                            "Country": "GB",
                            "PostalCode": "EC2A 4UX"
                        }
                    },
                    {
                        "Account": "400000014",
                        "Name": "GTA",
                        "FiscalName": "Kuoni Global Travel Services AG",
                        "Phone": "+34915226101",
                        "Email": "technical.support@gta-travel.com",
                        "Vat": "CHE-425.060.629",
                        "Location": {
                            "Address": "Überlandstrasse 360",
                            "City": "Zurich",
                            "Province": "",
                            "Country": "CH",
                            "PostalCode": "8051"
                        }
                    },
                    {
                        "Account": "400000481",
                        "Name": "Expedia",
                        "FiscalName": "EAN.com, LP",
                        "Phone": "0034912768716",
                        "Email": "aasupport@ean.com",
                        "Vat": "...",
                        "Location": {
                            "Address": "333 108th Ave N.E.",
                            "City": "Bellevue",
                            "Province": "",
                            "Country": "US",
                            "PostalCode": "98004"
                        }
                    },
                    {
                        "Account": "430004482",
                        "Name": "Smyrooms",
                        "FiscalName": "Travelnet DMCC",
                        "Phone": "+9718000320055",
                        "Email": "hotels.apac@smyrooms.com",
                        "Vat": "DMCC-265663",
                        "Location": {
                            "Address": "Mazaya Business Avenue, Building BB2",
                            "City": "Dubai",
                            "Province": "",
                            "Country": "AE",
                            "PostalCode": ".."
                        }
                    },
                    {
                        "Account": "400000023",
                        "Name": "Tourico",
                        "FiscalName": "TOURICO HOLIDAYS, INC",
                        "Phone": "+4076678700",
                        "Email": "Wendy.Jaimes@touricoholidays.com",
                        "Vat": "59-3260171",
                        "Location": {
                            "Address": "220 E. Central Pkwy. #4000 , FL 32701",
                            "City": "Altamonte Spring",
                            "Province": "Florida",
                            "Country": "US",
                            "PostalCode": "32701"
                        }
                    },
                    {
                        "Account": "430000065",
                        "Name": "Lots of hotels",
                        "FiscalName": "Lotsofhotels",
                        "Phone": "+971 4 5676300/ +20222649666",
                        "Email": "Premier.LOH@lotsofhotels.com",
                        "Vat": "91277",
                        "Location": {
                            "Address": "Shatha Tower | Level 17 | Suite 1714",
                            "City": "Dubai",
                            "Province": "",
                            "Country": "AE",
                            "PostalCode": "502115"
                        }
                    }
                ],
                "Zones": [],
                "Bookings": [
                    {
                        "Locator": "8HZDHX6C",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Mazen",
                            "Surname": "Almulhem"
                        },
                        "CreationDate": "2017-08-29T21:45:35.496Z",
                        "ModificationDate": "2017-08-29T21:45:35.496Z",
                        "ExpirationDate": "2017-08-30T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291197557_141113648520",
                                    "Status": "Confirmed",
                                    "Description": "The Meydan Hotel",
                                    "CheckInDate": "2017-09-02T00:00:00Z",
                                    "CheckOutDate": "2017-09-04T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 301.19,
                                            "Net": 301.19,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 293.13,
                                            "Net": 293.13,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 301.19,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 293.13,
                                            "Net": 293.13,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            },
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291197557_141113648521",
                                    "Status": "Confirmed",
                                    "Description": "The Meydan Hotel2",
                                    "CheckInDate": "2017-09-02T00:00:00Z",
                                    "CheckOutDate": "2017-09-04T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 301.19,
                                            "Net": 301.19,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 293.13,
                                            "Net": 293.13,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 301.19,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 293.13,
                                            "Net": 293.13,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "JI76CXUY",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "ahmed",
                            "Surname": "almutairi"
                        },
                        "CreationDate": "2017-08-29T21:48:03.182Z",
                        "ModificationDate": "2017-08-29T21:48:03.182Z",
                        "ExpirationDate": "2017-09-05T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291197664_141113703385",
                                    "Status": "Confirmed",
                                    "Description": "Rove Downtown Dubai",
                                    "CheckInDate": "2017-09-06T00:00:00Z",
                                    "CheckOutDate": "2017-09-09T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 252.24,
                                            "Net": 252.24,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 245.49,
                                            "Net": 245.49,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 252.24,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 245.49,
                                            "Net": 245.49,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "QIUODI12",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Mazen",
                            "Surname": "Almulhem"
                        },
                        "CreationDate": "2017-08-29T21:48:38.052Z",
                        "ModificationDate": "2017-08-29T21:48:38.052Z",
                        "ExpirationDate": "2017-09-01T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291197707_141113716886",
                                    "Status": "Confirmed",
                                    "Description": "The Meydan Hotel",
                                    "CheckInDate": "2017-09-04T00:00:00Z",
                                    "CheckOutDate": "2017-09-05T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 106.04,
                                            "Net": 106.04,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 103.2,
                                            "Net": 103.2,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 106.04,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 103.2,
                                            "Net": 103.2,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "VOEGHH9P",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "ghazi",
                            "Surname": "alqarni"
                        },
                        "CreationDate": "2017-08-29T22:31:40.561Z",
                        "ModificationDate": "2017-08-29T22:31:40.561Z",
                        "ExpirationDate": "2017-08-29T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "148-936075",
                                    "Status": "Confirmed",
                                    "Description": "Donatello Hotel",
                                    "CheckInDate": "2017-08-30T00:00:00Z",
                                    "CheckOutDate": "2017-09-04T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 592.2,
                                            "Net": 592.2,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 605.83,
                                            "Net": 605.83,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 592.2,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 605.83,
                                            "Net": 605.83,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "AEWHU51S",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Ebtisam",
                            "Surname": "Abulnaja"
                        },
                        "CreationDate": "2017-08-29T22:39:32.661Z",
                        "ModificationDate": "2017-08-29T22:39:32.661Z",
                        "ExpirationDate": "2017-08-29T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291199731_141114759983",
                                    "Status": "Confirmed",
                                    "Description":
                                    "JW Marriott Marquis Hotel Dubai",
                                    "CheckInDate": "2017-09-03T00:00:00Z",
                                    "CheckOutDate": "2017-09-07T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 507.95,
                                            "Net": 507.95,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 494.36,
                                            "Net": 494.36,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 507.95,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 494.36,
                                            "Net": 494.36,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "W2NAVY2H",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Anton",
                            "Surname": "Solodkov"
                        },
                        "CreationDate": "2017-08-29T22:44:05.591Z",
                        "ModificationDate": "2017-08-29T22:44:05.591Z",
                        "ExpirationDate": "2017-08-29T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "102-8124605",
                                    "Status": "Confirmed",
                                    "Description":
                                    "Eurostars Washington Irving",
                                    "CheckInDate": "2017-09-13T00:00:00Z",
                                    "CheckOutDate": "2017-09-14T00:00:00Z",
                                    "Zone": {
                                        "Code": "000354",
                                        "Name": "Granada, Granada, Spain"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 138.42,
                                            "Net": 138.42,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 141.24,
                                            "Net": 141.24,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 138.42,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 141.24,
                                            "Net": 141.24,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "BF58U45M",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Bernd",
                            "Surname": "Coir"
                        },
                        "CreationDate": "2017-08-29T22:50:15.244Z",
                        "ModificationDate": "2017-08-29T22:50:15.244Z",
                        "ExpirationDate": "2017-08-29T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "454602110",
                                    "Status": "Confirmed",
                                    "Description":
                                    "Pavillon Régent Petite France",
                                    "CheckInDate": "2017-09-17T00:00:00Z",
                                    "CheckOutDate": "2017-09-18T00:00:00Z",
                                    "Zone": {
                                        "Code": "033636",
                                        "Name": "Strasbourg, Grand-Est, France"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 197.37,
                                            "Net": 183.965026523872,
                                            "Commission": 13.4049734761285,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 192.64,
                                            "Net": 192.64,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 183.97,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 192.64,
                                            "Net": 192.64,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "430004482"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "KFYCBAU5",
                        "Status": "CancelledByCustomer",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Mohammed",
                            "Surname": "Qasem"
                        },
                        "CreationDate": "2017-08-30T02:03:52.699Z",
                        "ModificationDate": "2017-08-30T02:03:52.699Z",
                        "ExpirationDate": "0001-01-01T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "322-993758",
                                    "Status": "CancelledByCustomer",
                                    "Description": "Innotel Hotel",
                                    "CheckInDate": "2017-10-01T00:00:00Z",
                                    "CheckOutDate": "2017-10-05T00:00:00Z",
                                    "Zone": {
                                        "Code": "088990",
                                        "Name":
                                        "Singapore, Singapore Zone, Singapore"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "7E37V28I",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Turki",
                            "Surname": "Alfarraj"
                        },
                        "CreationDate": "2017-08-30T02:16:58.007Z",
                        "ModificationDate": "2017-08-30T02:16:58.007Z",
                        "ExpirationDate": "2017-08-30T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "454612734",
                                    "Status": "Confirmed",
                                    "Description":
                                    "JW Marriott Marquis Hotel Dubai",
                                    "CheckInDate": "2018-01-27T00:00:00Z",
                                    "CheckOutDate": "2018-02-02T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 2681.94,
                                            "Net": 2681.94,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 2815.69,
                                            "Net": 2815.69,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 2681.94,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 2815.69,
                                            "Net": 2815.69,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "430004482"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "44NKV7PP",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Salman",
                            "Surname": "Hassusah"
                        },
                        "CreationDate": "2017-08-30T02:24:14.644Z",
                        "ModificationDate": "2017-08-30T02:24:14.644Z",
                        "ExpirationDate": "2017-08-30T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291209682_141119501819",
                                    "Status": "Confirmed",
                                    "Description": "Saffron Hotel",
                                    "CheckInDate": "2017-08-30T00:00:00Z",
                                    "CheckOutDate": "2017-09-03T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 116.98,
                                            "Net": 116.98,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 113.85,
                                            "Net": 113.85,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 116.98,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 113.85,
                                            "Net": 113.85,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "44FUM35M",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "ALEKSANDR",
                            "Surname": "ELSHIN"
                        },
                        "CreationDate": "2017-08-30T02:26:51.494Z",
                        "ModificationDate": "2017-08-30T02:26:51.494Z",
                        "ExpirationDate": "2017-09-14T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "284-507697",
                                    "Status": "Confirmed",
                                    "Description": "Hotel Monterey Ginza",
                                    "CheckInDate": "2017-09-16T00:00:00Z",
                                    "CheckOutDate": "2017-09-17T00:00:00Z",
                                    "Zone": {
                                        "Code": "071774",
                                        "Name": "Chuo, Tokyo, Japan"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 199.15,
                                            "Net": 199.15,
                                            "Commission": 0,
                                            "CurrencyCode": "EUR"
                                        },
                                        "Sale": {
                                            "Gross": 243.32,
                                            "Net": 243.32,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 238.45,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 243.32,
                                            "Net": 243.32,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "M2FEZK8O",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Bandar",
                            "Surname": "Almalki"
                        },
                        "CreationDate": "2017-08-30T03:22:23.562Z",
                        "ModificationDate": "2017-08-30T03:22:23.562Z",
                        "ExpirationDate": "2017-09-04T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "23229999",
                                    "Status": "Confirmed",
                                    "Description":
                                    "Millennium Plaza Hotel Dubai",
                                    "CheckInDate": "2017-09-08T00:00:00Z",
                                    "CheckOutDate": "2017-09-09T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 147,
                                            "Net": 147,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 153.52,
                                            "Net": 153.52,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 147,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 153.52,
                                            "Net": 153.52,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000014"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "M8BI94XF",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Natalia",
                            "Surname": "Magai"
                        },
                        "CreationDate": "2017-08-30T03:40:17.193Z",
                        "ModificationDate": "2017-08-30T03:40:17.193Z",
                        "ExpirationDate": "2017-10-17T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "202-2196033",
                                    "Status": "Confirmed",
                                    "Description":
                                    "Hotel ibis Styles Berlin Alexanderplatz",
                                    "CheckInDate": "2017-10-18T00:00:00Z",
                                    "CheckOutDate": "2017-10-22T00:00:00Z",
                                    "Zone": {
                                        "Code": "080100",
                                        "Name": "Berlin, Land Berlin, Germany"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 312.6,
                                            "Net": 312.6,
                                            "Commission": 0,
                                            "CurrencyCode": "EUR"
                                        },
                                        "Sale": {
                                            "Gross": 381.92,
                                            "Net": 381.92,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 374.28,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 381.92,
                                            "Net": 381.92,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "16XPMDZE",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "KIM TATIANA PIAK ERNEST",
                            "Surname": "PAK MENOK PIAK KIRILL PIAK ANDREI"
                        },
                        "CreationDate": "2017-08-30T05:02:58.192Z",
                        "ModificationDate": "2017-08-30T05:02:58.192Z",
                        "ExpirationDate": "2017-09-27T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "23230314",
                                    "Status": "Confirmed",
                                    "Description": "Akasaka Excel Hotel Tokyu",
                                    "CheckInDate": "2017-09-29T00:00:00Z",
                                    "CheckOutDate": "2017-10-06T00:00:00Z",
                                    "Zone": {
                                        "Code": "071820",
                                        "Name": "Tokyo, Tokyo, Japan"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 2046,
                                            "Net": 2046,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 2131.25,
                                            "Net": 2131.25,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 2046,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 2131.25,
                                            "Net": 2131.25,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000014"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "C6ZKXWSJ",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Rasheed",
                            "Surname": "Banalyoh"
                        },
                        "CreationDate": "2017-08-30T05:03:25.078Z",
                        "ModificationDate": "2017-08-30T15:45:31.297Z",
                        "ExpirationDate": "2017-08-26T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291216694_141122411897",
                                    "Status": "Confirmed",
                                    "Description": "Manzil Downtown Dubai",
                                    "CheckInDate": "2017-09-02T00:00:00Z",
                                    "CheckOutDate": "2017-09-07T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 1879.04,
                                            "Net": 1879.04,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 1828.75,
                                            "Net": 1828.75,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 1879.04,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 1828.75,
                                            "Net": 1828.75,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "URBFMK5E",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Ahmed",
                            "Surname": "Altayyar"
                        },
                        "CreationDate": "2017-08-30T05:56:58.185Z",
                        "ModificationDate": "2017-08-30T05:56:58.185Z",
                        "ExpirationDate": "2017-09-25T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "454616569",
                                    "Status": "Confirmed",
                                    "Description": "Sura Hagia Sophia Hotel",
                                    "CheckInDate": "2017-09-27T00:00:00Z",
                                    "CheckOutDate": "2017-09-30T00:00:00Z",
                                    "Zone": {
                                        "Code": "088995",
                                        "Name": "Istanbul, Istanbul, Turkey"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 284.5,
                                            "Net": 284.5,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 292.54,
                                            "Net": 292.54,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 284.5,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 292.54,
                                            "Net": 292.54,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "430004482"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "7R4YJGFJ",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Shariffah Safinaz",
                            "Surname": "Mohamed"
                        },
                        "CreationDate": "2017-08-30T06:01:14.5Z",
                        "ModificationDate": "2017-08-30T06:01:14.5Z",
                        "ExpirationDate": "2017-09-07T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "23230594",
                                    "Status": "Confirmed",
                                    "Description": "Al Meroz Bangkok",
                                    "CheckInDate": "2017-09-11T00:00:00Z",
                                    "CheckOutDate": "2017-09-14T00:00:00Z",
                                    "Zone": {
                                        "Code": "080099",
                                        "Name": "Bangkok, Bangkok, Thailand"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 183.5,
                                            "Net": 183.5,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 191.15,
                                            "Net": 191.15,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 183.5,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 191.15,
                                            "Net": 191.15,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000014"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "ZV7D0YBO",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "DARIA",
                            "Surname": "TRUB"
                        },
                        "CreationDate": "2017-08-30T06:27:05.721Z",
                        "ModificationDate": "2017-08-30T06:27:05.721Z",
                        "ExpirationDate": "2017-08-30T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291219653_141123493275",
                                    "Status": "Confirmed",
                                    "Description":
                                    "Red and Blue Design Hotel Prague",
                                    "CheckInDate": "2017-09-10T00:00:00Z",
                                    "CheckOutDate": "2017-09-13T00:00:00Z",
                                    "Zone": {
                                        "Code": "067977",
                                        "Name":
                                        "Prague, Hlavní město Praha, Czechia"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 384.9,
                                            "Net": 384.9,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 373.69,
                                            "Net": 373.69,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 384.9,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 373.69,
                                            "Net": 373.69,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "8KDAYZGE",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Oleg",
                            "Surname": "Vysotckii"
                        },
                        "CreationDate": "2017-08-30T06:34:14.531Z",
                        "ModificationDate": "2017-08-30T06:34:14.531Z",
                        "ExpirationDate": "2016-11-24T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "BX06067",
                                    "Status": "Confirmed",
                                    "Description":
                                    "AZIMUT Hotel Olympic Moscow",
                                    "CheckInDate": "2017-12-30T00:00:00Z",
                                    "CheckOutDate": "2018-01-02T00:00:00Z",
                                    "Zone": {
                                        "Code": "079611",
                                        "Name": "Moscow, Moscow, Russia"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 130.98,
                                            "Net": 130.98,
                                            "Commission": 0,
                                            "CurrencyCode": "EUR"
                                        },
                                        "Sale": {
                                            "Gross": 163.5,
                                            "Net": 163.5,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 156.96,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 163.5,
                                            "Net": 163.5,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000024"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "ERJ88AT6",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Ilona",
                            "Surname": "Zakharevich"
                        },
                        "CreationDate": "2017-08-30T06:45:17.237Z",
                        "ModificationDate": "2017-08-30T06:45:17.237Z",
                        "ExpirationDate": "2017-09-11T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "214-701449",
                                    "Status": "Confirmed",
                                    "Description": "Oxygen Residence",
                                    "CheckInDate": "2017-09-11T00:00:00Z",
                                    "CheckOutDate": "2017-09-14T00:00:00Z",
                                    "Zone": {
                                        "Code": "067820",
                                        "Name": "Warsaw, Mazovia, Poland"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 382.68,
                                            "Net": 382.68,
                                            "Commission": 0,
                                            "CurrencyCode": "EUR"
                                        },
                                        "Sale": {
                                            "Gross": 467.93,
                                            "Net": 467.93,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 458.57,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 467.93,
                                            "Net": 467.93,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "HHIISUJG",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Aleksandr",
                            "Surname": "Sibatulin"
                        },
                        "CreationDate": "2017-08-30T06:57:34.367Z",
                        "ModificationDate": "2017-08-30T06:57:34.367Z",
                        "ExpirationDate": "2017-08-30T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291220826_141123879932",
                                    "Status": "Confirmed",
                                    "Description": "Hit Hotel",
                                    "CheckInDate": "2017-09-07T00:00:00Z",
                                    "CheckOutDate": "2017-09-08T00:00:00Z",
                                    "Zone": {
                                        "Code": "067820",
                                        "Name": "Warsaw, Mazovia, Poland"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 51.99,
                                            "Net": 51.99,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 50.48,
                                            "Net": 50.48,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 51.99,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 50.48,
                                            "Net": 50.48,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "K1AGZH2K",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Hai Yen",
                            "Surname": "Nguyen"
                        },
                        "CreationDate": "2017-08-30T07:04:19.346Z",
                        "ModificationDate": "2017-08-30T07:04:19.346Z",
                        "ExpirationDate": "2017-09-16T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "280-402504",
                                    "Status": "Confirmed",
                                    "Description": "Mantra 100 Exhibition",
                                    "CheckInDate": "2017-10-01T00:00:00Z",
                                    "CheckOutDate": "2017-10-03T00:00:00Z",
                                    "Zone": {
                                        "Code": "083810",
                                        "Name":
                                        "Melbourne, Victoria, Australia"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 307.17,
                                            "Net": 307.17,
                                            "Commission": 0,
                                            "CurrencyCode": "EUR"
                                        },
                                        "Sale": {
                                            "Gross": 375.6,
                                            "Net": 375.6,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 368.09,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 375.6,
                                            "Net": 375.6,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "XYYU9TV0",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Chien Quan",
                            "Surname": "Vu"
                        },
                        "CreationDate": "2017-08-30T07:04:55.989Z",
                        "ModificationDate": "2017-08-30T07:04:55.989Z",
                        "ExpirationDate": "2017-09-16T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "280-402505",
                                    "Status": "Confirmed",
                                    "Description": "Mantra 100 Exhibition",
                                    "CheckInDate": "2017-10-01T00:00:00Z",
                                    "CheckOutDate": "2017-10-03T00:00:00Z",
                                    "Zone": {
                                        "Code": "083810",
                                        "Name":
                                        "Melbourne, Victoria, Australia"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 307.17,
                                            "Net": 307.17,
                                            "Commission": 0,
                                            "CurrencyCode": "EUR"
                                        },
                                        "Sale": {
                                            "Gross": 375.6,
                                            "Net": 375.6,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 368.09,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 375.6,
                                            "Net": 375.6,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "LT9AYQTS",
                        "Status": "CancelledByCustomer",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Ibrahim",
                            "Surname": "Alkaran"
                        },
                        "CreationDate": "2017-08-30T07:36:55.087Z",
                        "ModificationDate": "2017-08-30T07:36:55.087Z",
                        "ExpirationDate": "2017-09-02T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "129070715",
                                    "Status": "CancelledByCustomer",
                                    "Description": "Towers Rotana",
                                    "CheckInDate": "2017-09-05T00:00:00Z",
                                    "CheckOutDate": "2017-09-11T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000023"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "J0KZIGC1",
                        "Status": "CancelledByCustomer",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Dania",
                            "Surname": "Alrajhi"
                        },
                        "CreationDate": "2017-08-30T07:53:58.56Z",
                        "ModificationDate": "2017-08-30T07:53:58.56Z",
                        "ExpirationDate": "2017-09-06T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291083558_141065471926",
                                    "Status": "CancelledByCustomer",
                                    "Description": "Roda Al Murooj",
                                    "CheckInDate": "2017-09-07T00:00:00Z",
                                    "CheckOutDate": "2017-09-14T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "6B9VW9EK",
                        "Status": "CancelledByCustomer",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Ahmed",
                            "Surname": "Alshaqha"
                        },
                        "CreationDate": "2017-08-30T07:59:57.95Z",
                        "ModificationDate": "2017-08-30T07:59:57.95Z",
                        "ExpirationDate": "2017-09-02T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "74-560549",
                                    "Status": "CancelledByCustomer",
                                    "Description":
                                    "Royal Arena Hotel & Resort Spa",
                                    "CheckInDate": "2017-09-06T00:00:00Z",
                                    "CheckOutDate": "2017-09-09T00:00:00Z",
                                    "Zone": {
                                        "Code": "094988",
                                        "Name": "Bodrum, Muğla, Turkey"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "SGYGRQ8A",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "ahmad",
                            "Surname": "neamah"
                        },
                        "CreationDate": "2017-08-30T08:04:35.909Z",
                        "ModificationDate": "2017-08-30T08:04:35.909Z",
                        "ExpirationDate": "2017-09-07T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "23231891",
                                    "Status": "Confirmed",
                                    "Description": "CVK Taksim Hotel Istanbul",
                                    "CheckInDate": "2017-09-08T00:00:00Z",
                                    "CheckOutDate": "2017-09-13T00:00:00Z",
                                    "Zone": {
                                        "Code": "088995",
                                        "Name": "Istanbul, Istanbul, Turkey"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 614.5,
                                            "Net": 614.5,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 641.78,
                                            "Net": 641.78,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 614.5,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 641.78,
                                            "Net": 641.78,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000014"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "K5VH3M4U",
                        "Status": "CancelledByCustomer",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Abdullah",
                            "Surname": "Almousa"
                        },
                        "CreationDate": "2017-08-30T08:23:58.636Z",
                        "ModificationDate": "2017-08-30T08:23:58.636Z",
                        "ExpirationDate": "2017-09-06T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "452585764",
                                    "Status": "CancelledByCustomer",
                                    "Description": "Hotel Ercilla",
                                    "CheckInDate": "2017-09-07T00:00:00Z",
                                    "CheckOutDate": "2017-09-09T00:00:00Z",
                                    "Zone": {
                                        "Code": "007493",
                                        "Name": "Bilbao, Biscay, Spain"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "430004482"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "CBQTYEXT",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Denis",
                            "Surname": "Urban"
                        },
                        "CreationDate": "2017-08-30T08:31:01.977Z",
                        "ModificationDate": "2017-08-30T08:31:01.977Z",
                        "ExpirationDate": "2017-08-30T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291225039_141125194523",
                                    "Status": "Confirmed",
                                    "Description": "Floris Hotel Ustel",
                                    "CheckInDate": "2017-09-24T00:00:00Z",
                                    "CheckOutDate": "2017-09-28T00:00:00Z",
                                    "Zone": {
                                        "Code": "074268",
                                        "Name":
                                        "City of Brussels, Belgium"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 646.57,
                                            "Net": 646.57,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 627.74,
                                            "Net": 627.74,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 646.57,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 627.74,
                                            "Net": 627.74,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "1IZY7J3C",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "EVGENII",
                            "Surname": "BIRIUKOV"
                        },
                        "CreationDate": "2017-08-30T08:46:47.139Z",
                        "ModificationDate": "2017-08-30T08:46:47.139Z",
                        "ExpirationDate": "2017-09-13T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "454633361",
                                    "Status": "Confirmed",
                                    "Description": "Hotel J",
                                    "CheckInDate": "2017-09-15T00:00:00Z",
                                    "CheckOutDate": "2017-09-25T00:00:00Z",
                                    "Zone": {
                                        "Code": "067395",
                                        "Name":
                                        "Nacka Municipality, Stockholm, Sweden"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 1893.86,
                                            "Net": 1893.86,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 1983.1,
                                            "Net": 1983.1,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 1893.86,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 1983.1,
                                            "Net": 1983.1,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "430004482"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "4QF2IS03",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Arseniy",
                            "Surname": "Glazkov"
                        },
                        "CreationDate": "2017-08-30T08:51:02.881Z",
                        "ModificationDate": "2017-08-30T08:51:02.881Z",
                        "ExpirationDate": "2017-10-12T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "255-1390043",
                                    "Status": "Confirmed",
                                    "Description": "Chicago's Essex Inn",
                                    "CheckInDate": "2017-10-16T00:00:00Z",
                                    "CheckOutDate": "2017-10-20T00:00:00Z",
                                    "Zone": {
                                        "Code": "056324",
                                        "Name":
                                        "Chicago, Illinois, United States"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 676.88,
                                            "Net": 676.88,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 690.69,
                                            "Net": 690.69,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 676.88,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 690.69,
                                            "Net": 690.69,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000001"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "U6GCW7Q8",
                        "Status": "CancelledBySystemOrAdmin",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "Huseyn",
                            "Surname": "Asgarov"
                        },
                        "CreationDate": "2017-08-30T08:55:39.649Z",
                        "ModificationDate": "2017-08-30T08:55:39.649Z",
                        "ExpirationDate": "2017-08-31T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "451660687",
                                    "Status": "CancelledBySystemOrAdmin",
                                    "Description": "Hotel Patria",
                                    "CheckInDate": "2017-09-03T00:00:00Z",
                                    "CheckOutDate": "2017-09-17T00:00:00Z",
                                    "Zone": {
                                        "Code": "010919",
                                        "Name": "Rome, Lazio, Italy"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "430004482"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "3EC8AJN7",
                        "Status": "CancelledByCustomer",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Ahmed",
                            "Surname": "Alghfeli"
                        },
                        "CreationDate": "2017-08-30T09:26:06.232Z",
                        "ModificationDate": "2017-08-30T09:26:06.232Z",
                        "ExpirationDate": "2017-09-09T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "454134228",
                                    "Status": "CancelledByCustomer",
                                    "Description":
                                    "The Ritz-Carlton Executive Residences",
                                    "CheckInDate": "2017-09-10T00:00:00Z",
                                    "CheckOutDate": "2017-09-15T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "430004482"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "MQX3E38O",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "nbgg",
                            "Surname": "Dfh"
                        },
                        "CreationDate": "2017-08-30T09:28:29.893Z",
                        "ModificationDate": "2017-08-30T09:28:29.893Z",
                        "ExpirationDate": "2017-09-06T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291227929_141126053112",
                                    "Status": "Confirmed",
                                    "Description":
                                    "Al Seef Resort & Spa by Andalus",
                                    "CheckInDate": "2017-09-07T00:00:00Z",
                                    "CheckOutDate": "2017-09-08T00:00:00Z",
                                    "Zone": {
                                        "Code": "016887",
                                        "Name":
                                        "Abu Dhabi, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 67.74,
                                            "Net": 67.74,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 65.93,
                                            "Net": 65.93,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 67.74,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 65.93,
                                            "Net": 65.93,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "QZNYV13L",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "khaled",
                            "Surname": "alfaifi"
                        },
                        "CreationDate": "2017-08-31T06:37:28.779Z",
                        "ModificationDate": "2017-08-31T06:37:28.779Z",
                        "ExpirationDate": "2017-08-31T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "454845741",
                                    "Status": "Confirmed",
                                    "Description": "Donatello Hotel",
                                    "CheckInDate": "2017-09-30T00:00:00Z",
                                    "CheckOutDate": "2017-10-04T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 199.12,
                                            "Net": 199.12,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 209.05,
                                            "Net": 209.05,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 199.12,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 209.05,
                                            "Net": 209.05,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "430004482"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "Locator": "KWSMDU2D",
                        "Status": "CancelledBySystemOrAdmin",
                        "Customer": {
                            "Account": "430000392"
                        },
                        "Holder": {
                            "Name": "AZHAR",
                            "Surname": "KUANYSHBAYEVA"
                        },
                        "CreationDate": "2017-08-31T06:44:31.65Z",
                        "ModificationDate": "2017-08-31T06:44:31.65Z",
                        "ExpirationDate": "2017-09-08T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator": "454220054",
                                    "Status": "CancelledBySystemOrAdmin",
                                    "Description": "Imperial Palace Hotel",
                                    "CheckInDate": "2017-09-11T00:00:00Z",
                                    "CheckOutDate": "2017-09-15T00:00:00Z",
                                    "Zone": {
                                        "Code": "094989",
                                        "Name": "Yerevan, Yerevan, Armenia"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 0,
                                            "Net": 0,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "430004482"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        ''')
        small_set_complete_no_zones = ('''{
            "Export": {
                "ExportId": "202bde2c-b35e-4e18-8a8e-92f4bbe71f3d",
                "Track": "rrt-0ecb05c66906b353e-a-eu-19045-17256595-1",
                "ExportedAt": "2017-08-31 07:30:16.305",
                "Customers": [
                    {
                        "Account": "430000392",
                        "Name": "Ostrovok B2B",
                        "LegalName": "Emerging Travel",
                        "Phone": "+74992156525",
                        "Email": "res@ostrovok.ru",
                        "Vat": "XXX",
                        "Location": {
                            "Address": "3500 S. DuPont Hwy",
                            "City": "Dover (Delaware)",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "19901"
                        }
                    },
                    {
                        "Account": "430004478",
                        "Name": "Nustay",
                        "LegalName": "Nustay",
                        "Phone": "+45 31 18 89 89",
                        "Email": "dc@nustay.com",
                        "Vat": "36090316",
                        "Location": {
                            "Address": "test",
                            "City": "test",
                            "Province": null,
                            "Country": "DK",
                            "PostalCode": "test"
                        }
                    },
                    {
                        "Account": "430004476",
                        "Name": "HotelTravelAgent.net",
                        "LegalName": "HotelTravelAgent",
                        "Phone": "1-212-989-1386 / 866-397-1300",
                        "Email": "mfriedman@hoteltravelagent.net",
                        "Vat": "461639461",
                        "Location": {
                            "Address": "1472 47th Street, Brooklyn",
                            "City": "New York",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "11219"
                        }
                    },
                    {
                        "Account": "430000450",
                        "Name": "Tektraveler International",
                        "LegalName": "Tektraveler International LLC",
                        "Phone": "001 (281) 9078620",
                        "Email": "andre@tektraveler.com",
                        "Vat": "46-2774812",
                        "Location": {
                            "Address": "The Woodlands, TX",
                            "City": "Houston",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "77380"
                        }
                    },
                    {
                        "Account": "430004477",
                        "Name": "IBC Hotels",
                        "LegalName": "IBC Hospitality",
                        "Phone": "602-944-1500 ext. 215",
                        "Email": "pbarnhill@innsuites.com",
                        "Vat": "34-6647590",
                        "Location": {
                            "Address": "1625 E. Northern Ave 105",
                            "City": "Phoenix",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "85020"
                        }
                    },
                    {
                        "Account": "430004475",
                        "Name": "Hotelspro",
                        "LegalName": "Hotelspro DMCC",
                        "Phone": "05309552463",
                        "Email": "emre.senol@metglobal.com",
                        "Vat": "xxxxxx",
                        "Location": {
                            "Address":
                            "Saba Tower 1, Cluster E, Office 2602, Jumeirah",
                            "City": "Dubai",
                            "Province": null,
                            "Country": "AE",
                            "PostalCode": "336315"
                        }
                    },
                    {
                        "Account": "430004474",
                        "Name": "Haoqiao",
                        "LegalName":
                        "Beijing Haoqiao international Travel Agency Limited",
                        "Phone": "010-62016080",
                        "Email": "zhuweiyan@haoqiao.cn",
                        "Vat": "110106355274393",
                        "Location": {
                            "Address": "Room 611, F6, Changxin Mansion, 69",
                            "City": "Beijing",
                            "Province": null,
                            "Country": "CN",
                            "PostalCode": "xx"
                        }
                    },
                    {
                        "Account": "430000438",
                        "Name": "Almosafer B2B",
                        "LegalName": "Al Tayyar Travel Group",
                        "Phone": "+20101333304",
                        "Email": "ahmed.fouad@almosaferer.com",
                        "Vat": "1010148039",
                        "Location": {
                            "Address": "Ulaya, Riyadh KSA",
                            "City": "Rihad",
                            "Province": null,
                            "Country": "SA",
                            "PostalCode": "XXXX"
                        }
                    },
                    {
                        "Account": "430000299",
                        "Name": "Italcamel",
                        "LegalName": "Italcamel Travel Agency s.r.l.",
                        "Phone": "00390541661711",
                        "Email": "simona.gagliazzo@italcamel.com",
                        "Vat": "1227490404",
                        "Location": {
                            "Address": "viale Dante, 155",
                            "City": "Riccione",
                            "Province": null,
                            "Country": "IT",
                            "PostalCode": "00390541661711"
                        }
                    },
                    {
                        "Account": "430000483",
                        "Name": "Viagens Mark Operadora",
                        "LegalName":
                        "Viagens Mark Operadora de Turismo e Receptivo Eireli",
                        "Phone": "0055 85 3242-7353",
                        "Email": "aline@viagensmark.com.br",
                        "Vat": "16.584.066/0001-06",
                        "Location": {
                            "Address":
                            "Rua Pe. Carlos Quixada, 175 - Parangaba",
                            "City": "Fortaleza",
                            "Province": null,
                            "Country": "BR",
                            "PostalCode": "60740-540"
                        }
                    },
                    {
                        "Account": "430004480",
                        "Name": "Travel Experience",
                        "LegalName": "Travel Experience",
                        "Phone": "xxxxx",
                        "Email": "dave@travelexperience.be",
                        "Vat": "Be 0460.860.460",
                        "Location": {
                            "Address": "Astridplein 4",
                            "City": "Grobbendonk",
                            "Province": null,
                            "Country": "BE",
                            "PostalCode": "2280"
                        }
                    },
                    {
                        "Account": "430004473",
                        "Name": "Check In Viajes",
                        "LegalName": "Operadora de Viajes Check In SA de CV",
                        "Phone": "(33) 3616 7244",
                        "Email": "victor@checkinviajes.mx",
                        "Vat": "OVC140325UE0",
                        "Location": {
                            "Address":
                            "Av. Guadalupe 6340-6 - Centro Com. Plaza Cibeles",
                            "City": "Zapopan Jalisco",
                            "Province": null,
                            "Country": "MX",
                            "PostalCode": "45010"
                        }
                    },
                    {
                        "Account": "430000042",
                        "Name": "Explore the Wonders",
                        "LegalName": "Explore the Wonders",
                        "Phone": "+971 6 557 3938",
                        "Email": "desmond@etws.ae",
                        "Vat": "08496",
                        "Location": {
                            "Address": "Sharjah Airport International Free",
                            "City": "Sharjah",
                            "Province": null,
                            "Country": "AE",
                            "PostalCode": "P.O.Box 120924"
                        }
                    },
                    {
                        "Account": "430004479",
                        "Name": "Rocket Miles",
                        "LegalName": "Rocket Trave, Inc.",
                        "Phone": "0013308583659",
                        "Email": "john@rocketmiles.com",
                        "Vat": "461105421",
                        "Location": {
                            "Address": "641 W, Lake Street",
                            "City": "Chicago",
                            "Province": null,
                            "Country": "US",
                            "PostalCode": "IL 60661"
                        }
                    },
                    {
                        "Account": "430004481",
                        "Name": "eHotel AG",
                        "LegalName": "eHotel AG",
                        "Phone": "+49 30 47373 146",
                        "Email": "r.gegenfurtner@ehotel.de",
                        "Vat": "HRB78969",
                        "Location": {
                            "Address": "Greifswalder Str. 208",
                            "City": "Berlin",
                            "Province": null,
                            "Country": "DE",
                            "PostalCode": "10405"
                        }
                    }
                ],
                "Suppliers": [
                    {
                        "Account": "400000481",
                        "Name": "Expedia",
                        "FiscalName": "EAN.com, LP",
                        "Phone": "0034912768716",
                        "Email": "aasupport@ean.com",
                        "Vat": "...",
                        "Location": {
                            "Address": "333 108th Ave N.E.",
                            "City": "Bellevue",
                            "Province": "",
                            "Country": "US",
                            "PostalCode": "98004"
                        }
                    }
                ],
                "Zones": [],
                "Bookings": [
                    {
                        "Locator": "8Hpeper",
                        "Status": "Confirmed",
                        "Customer": {
                            "Account": "430000438"
                        },
                        "Holder": {
                            "Name": "Mazen",
                            "Surname": "Almulhem"
                        },
                        "CreationDate": "2017-08-29T21:45:35.496Z",
                        "ModificationDate": "2017-08-29T21:45:35.496Z",
                        "ExpirationDate": "2017-08-30T00:00:00Z",
                        "Services": [
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291197557_141113648520",
                                    "Status": "Confirmed",
                                    "Description": "The Meydan Hotel",
                                    "CheckInDate": "2017-09-02T00:00:00Z",
                                    "CheckOutDate": "2017-09-04T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 301.19,
                                            "Net": 301.19,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 293.13,
                                            "Net": 293.13,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 301.19,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 293.13,
                                            "Net": 293.13,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            },
                            {
                                "Accommodation": {
                                    "ExternalLocator":
                                    "291197557_141113648521",
                                    "Status": "Confirmed",
                                    "Description": "The Meydan Hotel2",
                                    "CheckInDate": "2017-09-02T00:00:00Z",
                                    "CheckOutDate": "2017-09-04T00:00:00Z",
                                    "Zone": {
                                        "Code": "016891",
                                        "Name":
                                        "Dubai, Dubai, United Arab Emirates"
                                    },
                                    "Price": {
                                        "Purchase": {
                                            "Gross": 301.19,
                                            "Net": 301.19,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 293.13,
                                            "Net": 293.13,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "PriceCompanyCurrency": {
                                        "Purchase": {
                                            "Net": 301.19,
                                            "CurrencyCode": "USD"
                                        },
                                        "Sale": {
                                            "Gross": 293.13,
                                            "Net": 293.13,
                                            "Commission": 0,
                                            "CurrencyCode": "USD"
                                        }
                                    },
                                    "Supplier": {
                                        "Account": "400000481"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        ''')
        self._zones = zones
        self._customers = customers
        self._suppliers = suppliers
        self._bookings = bookings
        self._complete_no_zones = complete_no_zones
        self._small_set_complete_no_zones = small_set_complete_no_zones
        # http://localhost:8069/complete_no_zones

    @app.route('/zones', methods=['GET'])
    def items_zones(self, request):
        Api_Key = 'FfyYt9iWYHSGuCTocXOpILcdCo8skC7a'
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Api-Key', Api_Key)
        return self._zones

    @app.route('/customers', methods=['GET'])
    def items_customers(self, request):
        Api_Key = 'FfyYt9iWYHSGuCTocXOpILcdCo8skC7a'
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Api-Key', Api_Key)
        return self._customers

    @app.route('/suppliers', methods=['GET'])
    def items_suppliers(self, request):
        Api_Key = 'FfyYt9iWYHSGuCTocXOpILcdCo8skC7a'
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Api-Key', Api_Key)
        return self._suppliers

    @app.route('/bookings', methods=['GET'])
    def items_bookings(self, request):
        Api_Key = 'FfyYt9iWYHSGuCTocXOpILcdCo8skC7a'
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Api-Key', Api_Key)
        return self._bookings

    @app.route('/complete_no_zones', methods=['GET'])
    def items_complete_no_zones(self, request):
        Api_Key = 'FfyYt9iWYHSGuCTocXOpILcdCo8skC7a'
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Api-Key', Api_Key)
        return self._complete_no_zones

    @app.route('/small_set', methods=['GET'])
    def small_set_complete_no_zones(self, request):
        Api_Key = 'FfyYt9iWYHSGuCTocXOpILcdCo8skC7a'
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Api-Key', Api_Key)
        return self._small_set_complete_no_zones

    @app.route('/send_confirm', methods=['PUT'])
    def send_confirm(self, request):
        import logging
        _log = logging.getLogger(__name__)
        _log.info('X' * 80)
        _log.info(('req', request))
        _log.info('X' * 80)
        Api_Key = 'FfyYt9iWYHSGuCTocXOpILcdCo8skC7a'
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Api-Key', Api_Key)
        return True


if __name__ == '__main__':
    store = ItemStore()
    store.app.run('localhost', 8080)
