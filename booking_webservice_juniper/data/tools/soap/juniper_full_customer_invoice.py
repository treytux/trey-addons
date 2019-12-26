# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import suds


service_url = "http://booking.methabook.com/wsExportacion/wsInvoices.asmx" \
              "?wsdl"
service_user = "OdooErp"
service_password = "Joaquin2015"


def main():
    # _log = log.init_logger('suds.client', debug=True)
    client = suds.client.Client(service_url)
    response = client.service.GetInvoices(
        user=service_user,
        password=service_password,
        InvoiceSeries=None,
        InvoiceNumberFrom=None,
        InvoiceNumberTo=None,
        InvoiceDateFrom='20150101',
        InvoiceDateTo='20150920',
        InvoiceIdNumberFrom=None,
        InvoiceIdNumberTo=None,
        BeginTravelDate=None,
        EndTravelDate=None,
        customerId=None,
        ExportMode='C',
        channel=None)
    if response and response['wsResult']:
        customer_invoice_list = response['wsResult']['Invoices']['Invoice']
        print "Numero de registros:%s" % len(customer_invoice_list)
        for customer_invoice in customer_invoice_list:
            print "Factura: %s Moneda: %s Importe: %s" % (
                customer_invoice._InvoiceNumber,
                customer_invoice._Currency,
                customer_invoice._TotalInvoiceAmount)


if __name__ == '__main__':
    main()
