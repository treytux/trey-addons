# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
try:
    import xmltodict
    import suds
    from openerp import exceptions, _
    import logging
    _log = logging.getLogger(__name__)
except ImportError:
    from . import log as log
    _log = log.init_logger('suds.client', debug=True)


class Juniper(object):
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

    def customer(self, customerType=None, creationDateFrom=None,
                 creationDateTo=None, id=None, ExportMode='C'):
        """
        ----------------------------------------------------------------------
        Consultar datos de cliente
        ----------------------------------------------------------------------
        :param customerType: Tipo de cliente
        :param creationDateFrom: Creado desde
        :param creationDateTo:  Creado hasta
        :param id: Id del cliente
        :param ExportMode: Tipo de exportacion E=Exportacion C=Consulta
        ----------------------------------------------------------------------
        :return: Diccionario de valores
        ----------------------------------------------------------------------
        """
        try:
            url = '%s/wsExportacion/wsCustomers.asmx?wsdl' % self.url
            client = suds.client.Client(url, retxml=True)
            response = client.service.getCustomerList(
                url=url, user=self.user, password=self.password,
                customerType=customerType, creationDateFrom=creationDateFrom,
                creationDateTo=creationDateTo, id=id, ExportMode=ExportMode)
        except RuntimeError as detail:
            _log.critical(
                'WebService Connection Error', detail)
            raise
        if response:
            x = xmltodict.parse(response)
            lr = x['soap:Envelope']['soap:Body']['getCustomerListResponse']
            re = lr['getCustomerListResult']['wsResult']
            return re['Customers']['Customer']
        else:
            return []

    def customerinvoice(self, InvoiceSeries=None,
                        InvoiceNumberFrom=None, InvoiceNumberTo=None,
                        InvoiceDateFrom=None, InvoiceDateTo=None,
                        InvoiceIdNumberFrom=None, InvoiceIdNumberTo=None,
                        BeginTravelDate=None, EndTravelDate=None,
                        CustomerID=None, ExportMode='C', channel=None):
        """
        ----------------------------------------------------------------------
        Consulta de facturas de cliente (no se usa)
        ----------------------------------------------------------------------
        :param InvoiceSeries: Serie de facturacion
        :param InvoiceNumberFrom: Desde numero de factura
        :param InvoiceNumberTo: Hasta numero de factura
        :param InvoiceDateFrom: Desde fecha factura
        :param InvoiceDateTo: Hasta fecha de factura
        :param InvoiceIdNumberFrom: Desde el Id
        :param InvoiceIdNumberTo: Hasta el id
        :param BeginTravelDate: Desde fecha inicio de servicio
        :param EndTravelDate: Hasta fecha fin de servicio
        :param CustomerID: Id de cliente
        :param ExportMode: Tipo de exportacion
        :param channel: Canal de venta
        ----------------------------------------------------------------------
        :return: Diccionario de valores
        ----------------------------------------------------------------------
        """

        try:
            url = '%s/wsExportacion/wsInvoices.asmx?wsdl' % self.url
            suds.client.Client(url)
            # TODO: Terminar la llamada al metodo
        except RuntimeError as detail:
            _log.critical('WebService Connection Error', detail)
            raise

    def customerpayments(self, CreationDateFrom=None,
                         CreationDateTo=None, CreationTimeFrom=None,
                         CreationTimeTo=None, Customerid=None, PaymentId=None,
                         CustomerType=None, TypeOfPayment=None, ExportMode='C',
                         channel=None, invoiceId=None):
        """
        ----------------------------------------------------------------------
        Consulta datos de pago (no se usa)
        ----------------------------------------------------------------------
        :param CreationDateFrom:
        :param CreationDateTo:
        :param CreationTimeFrom:
        :param CreationTimeTo:
        :param Customerid:
        :param PaymentId:
        :param CustomerType:
        :param TypeOfPayment:
        :param ExportMode:
        :param channel:
        :param invoiceId:
        ----------------------------------------------------------------------
        :return:
        ----------------------------------------------------------------------
        """

        try:
            url = '%s/wsExportacion/wsInvoices.asmx?wsdl' % self.url
            suds.client.Client(url)
            # TODO: Terminar la llamada al metodo
        except RuntimeError as detail:
            _log.critical('WebService Connection Error', detail)
            raise

    def supplier(self, SupplierId=None, ExportMode='C'):
        """
        ----------------------------------------------------------------------
        Consulta de datos de proveedor
        ----------------------------------------------------------------------
        :param SupplierId: Id del proveedor
        :param ExportMode: E o C, siempre en modo consulta C
        ----------------------------------------------------------------------
        :return: Diccionario de datos
        ----------------------------------------------------------------------
        """
        try:
            url = '%s/wsExportacion/wsSuppliers.asmx?wsdl' % self.url
            client = suds.client.Client(url, retxml=True)
            response = client.service.getSupplierList(
                user=str(self.user), password=str(self.password),
                SupplierId=str(SupplierId), ExportMode=str(ExportMode))
        except RuntimeError as detail:
            _log.critical('WebService Connection Error', detail)
            raise
        if response:
            x = xmltodict.parse(response)
            lr = x['soap:Envelope']['soap:Body']['getSupplierListResponse']
            re = lr['getSupplierListResult']['wsResult']
            return re['Suppliers']['Supplier']
        else:
            return[]

    def supplierinvoice(self, InvoiceFileNumberFrom=None,
                        InvoiceFileNumberTo=None, InvoiceNumer=None,
                        Supplier_Id=None, InvoiceDateFrom=None,
                        InvoiceDateTo=None, InvoiceRegistrationDateFrom=None,
                        InvoiceRegistrationDateTo=None, BookingCode=None,
                        ExportMode='C', channel=None):
        """
        ----------------------------------------------------------------------
        Consultar factura de proveedor (no se usa)
        ----------------------------------------------------------------------
        :param InvoiceFileNumberFrom:
        :param InvoiceFileNumberTo:
        :param InvoiceNumer:
        :param Supplier_Id:
        :param InvoiceDateFrom:
        :param InvoiceDateTo:
        :param InvoiceRegistrationDateFrom:
        :param InvoiceRegistrationDateTo:
        :param BookingCode:
        :param ExportMode:
        :param channel:
        ----------------------------------------------------------------------
        :return:
        ----------------------------------------------------------------------
        """

        try:
            url = '%s/wsExportacion/wsInvoices.asmx?wsdl' % self.url
            suds.client.Client(url)
            # TODO: Terminar la llamada al metodo
        except RuntimeError as detail:
            _log.critical('WebService Connection Error', detail)
            raise

    def supplierpayment(self, CreationDateFrom=None,
                        CreationDateTo=None, CreationTimeFrom=None,
                        CreationTimeTo=None, PaymentId=None, SupplierID=None,
                        TypeOfPayment=None, ExportMode='C', channel=None):
        """
        ----------------------------------------------------------------------
        Consultar pago de proveedor (no se usa)
        ----------------------------------------------------------------------
        :param CreationDateFrom:
        :param CreationDateTo:
        :param CreationTimeFrom:
        :param CreationTimeTo:
        :param PaymentId:
        :param SupplierID:
        :param TypeOfPayment:
        :param ExportMode:
        :param channel:
        ----------------------------------------------------------------------
        :return:
        ----------------------------------------------------------------------
        """

        # url = '%s/wsExportacion/wsInvoices.asmx?wsdl' % self.url
        # client = suds.client.Client(url)
        # TODO: Terminar la llamada al metodo
        pass

    def booking(self, BookingDateFrom=None, BookingDateTo=None,
                BeginTravelDate=None, EndTravelDate=None,
                LastModifiedDateFrom=None, LastModifiedDateTo=None,
                BookingCode=None, Status=None, id=None, ExportMode='C',
                channel=None, ModuleType=None, ManualUpdate=None):
        """
        ----------------------------------------------------------------------
        Consulta de reservas
        ----------------------------------------------------------------------
        :param BookingDateFrom: Creado desde fecha
        :param BookingDateTo: Creado hasta fecha
        :param BeginTravelDate: Desde fecha inicio de servicio
        :param EndTravelDate: Hasta fecha fin de servicio
        :param LastModifiedDateFrom: Desde fecha de modificacion
        :param LastModifiedDateTo: Hasta fecha de modificacion
        :param BookingCode: Codigo de reserva
        :param Status: Estado de la reserva
        :param id: Identificador de reserva
        :param ExportMode: Tipo de exportacion
        :param channel: Canal
        :param ModuleType:
        ----------------------------------------------------------------------
        :return: Diccionario de datos de la reserva
        ----------------------------------------------------------------------
        """
        try:
            url = '%s/wsExportacion/wsBookings.asmx?wsdl' % self.url
            client = suds.client.Client(url, retxml=True)
            response = client.service.getBookings(
                user=self.user, password=self.password,
                BookingDateFrom=BookingDateFrom,
                BookingDateTo=BookingDateTo, BeginTravelDate=BeginTravelDate,
                EndTravelDate=EndTravelDate,
                LastModifiedDateFrom=LastModifiedDateFrom,
                LastModifiedDateTo=LastModifiedDateTo, BookingCode=BookingCode,
                Status=Status, id=id, ExportMode=ExportMode, channel=channel,
                ModuleType=ModuleType)
        except RuntimeError as detail:
            _log.critical('WebService Connection Error' % detail)
            raise
        except Exception as ex:
            _log.info('General error in Juniper WebService code "%s": %s' % (
                BookingCode, ex))
            return False
        if not response:
            return []
        x = xmltodict.parse(response)
        lr = x['soap:Envelope']['soap:Body']['getBookingsResponse']
        if 'Bookings' not in lr['getBookingsResult']['wsResult']:
            if not ManualUpdate:
                # Error from juniper api:
                # ('re', OrderedDict([(u'@xmlns', u''),
                # ('#text', u'Object reference not set to an instance of an '
                #             'object.')]))
                return []
            raise exceptions.Warning(
                _('No bookings found !'),
                _('Try with another dates range or booking code'))
        return lr['getBookingsResult']['wsResult']['Bookings']['Booking']

    def booking_solole(
        self, BookingDateFrom=None, BookingDateTo=None,
        BeginTravelDate=None, EndTravelDate=None,
        LastModifiedDateFrom=None, LastModifiedDateTo=None,
        BookingCode=None, Status=None, id=None, ExportMode='C',
            channel=None, ModuleType=None, ManualUpdate=None):
        """
        ----------------------------------------------------------------------
        Consulta de reservas De SOLOLE
        ----------------------------------------------------------------------
        :param BookingDateFrom: Creado desde fecha
        :param BookingDateTo: Creado hasta fecha
        :param BeginTravelDate: Desde fecha inicio de servicio
        :param EndTravelDate: Hasta fecha fin de servicio
        :param LastModifiedDateFro4: Desde fecha de modificacion
        :param LastModifiedDateTo: Hasta fecha de modificacion
        :param BookingCode: Codigo de reserva
        :param Status: Estado de la reserva
        :param id: Identificador de reserva
        :param ExportMode: Tipo de exportacion
        :param channel: Canal
        :param ModuleType:
        ----------------------------------------------------------------------
        :return: Diccionario de datos de la reserva
        ----------------------------------------------------------------------
        """
        try:
            url = '%s/wsExportacion/wsBookings.asmx?wsdl' % self.url
            client = suds.client.Client(url, retxml=True)
            response = client.service.getBookings(
                user=self.user,
                password=self.password,
                BookingDateFrom=BookingDateFrom,
                BookingDateTo=BookingDateTo,
                BeginTravelDate=BeginTravelDate,
                EndTravelDate=EndTravelDate,
                LastModifiedDateFrom=LastModifiedDateFrom,
                LastModifiedDateTo=LastModifiedDateTo,
                BookingCode=unicode(BookingCode),
                Status=Status,
                id=id,
                ExportMode=ExportMode,
                channel=channel,
                ModuleType=ModuleType)

        except RuntimeError as detail:
            _log.critical(
                'WebService Connection Error in Solole-Juniper' % detail)
            raise
        except Exception as ex:
            _log.info(
                'General error in Solole-Juniper WebService code "%s": %s' % (
                    BookingCode, ex))
            return False
        if not response:
            return []
        x = xmltodict.parse(response)
        lr = x['soap:Envelope']['soap:Body']['getBookingsResponse']
        if 'Bookings' not in lr['getBookingsResult']['wsResult']:
            if not ManualUpdate:
                # Error from juniper api:
                # ('re', OrderedDict([(u'@xmlns', u''),
                # ('#text', u'Object reference not set to an instance of an '
                #             'object.')]))
                return []
            _log.info(('No bookings found! Try with another booking code'))
            raise exceptions.Warning(
                _('No bookings found !'),
                _('Try with another dates range or booking code'))
        return lr['getBookingsResult']['wsResult']['Bookings']['Booking']


if __name__ == '__main__':
    from pprint import pprint

    juniper = Juniper(
        url='http://booking.methabook.com',
        user='OdooErp',
        password='Joaquin2015')
    res = juniper.booking(
        BeginTravelDate='20170101',
        EndTravelDate='20170102',
        ExportMode='C')
    # res = juniper.booking(
    #     BookingDateFrom='2017-05-16T00:00:01',
    #     # BookingDateTo='2017-05-15T00:00:01',
    #     ExportMode='C')
    pprint(res)
