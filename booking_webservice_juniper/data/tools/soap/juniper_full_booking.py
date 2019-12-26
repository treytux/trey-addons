# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import suds
import json
from suds.sudsobject import asdict

service_url = "http://booking.methabook.com/wsExportacion/wsBookings.asmx" \
              "?wsdl"
service_user = "OdooErp"
service_password = "Joaquin2015"


def recursive_asdict(d):
    """Convert Suds object into serializable format."""
    out = {}
    for k, v in asdict(d).iteritems():
        if hasattr(v, '__keylist__'):
            out[k] = recursive_asdict(v)
        elif isinstance(v, list):
            out[k] = []
            for item in v:
                if hasattr(item, '__keylist__'):
                    out[k].append(recursive_asdict(item))
                else:
                    out[k].append(item)
        else:
            out[k] = v
    return out


def suds_to_json(data):
    return json.dumps(recursive_asdict(data))


def main():

    # Asi se define el log del cliente SOAP
    # TODO: Tengo que ver como se utiliza el log SOAP
    # _log = logging.getLogger('suds.client').setLevel(logging.INFO)
    try:
        client = suds.client.Client(service_url)
        response = client.service.getBookings(
            user=service_user,
            password=service_password,
            BookingDateFrom=None,
            BookingDateTo=None,
            BeginTravelDate=None,
            EndTravelDate=None,
            LastModifiedDateFrom=None,
            LastModifiedDateTo=None,
            BookingCode='9521Q3',
            Status=None,
            id=None,
            ExportMode='C',
            channel=None,
            ModuleType=None)
    except RuntimeError as detail:
        print 'Error en la conexion a WebService', detail
        return
    if response and response['wsResult']:
        print response
        booking_list = response['wsResult']['Bookings']['Booking']
        print "Numero de registros: %s" % len(booking_list)
        for booking in booking_list:
            print type(booking)
            print recursive_asdict(booking)
            print(
                "Codigo de Reserva: %s, Inicio: %s, Final: %s Creado: %s "
                "Estado: %s" % (
                    booking._BookingCode,
                    booking['Lines']['Line'].BeginTravelDate,
                    booking['Lines']['Line'].EndTravelDate,
                    booking._BookingDate,
                    booking._Status))


if __name__ == '__main__':
    main()
