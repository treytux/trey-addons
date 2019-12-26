# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import suds


service_url = "http://booking.methabook.com/wsExportacion/wsInvoices.asmx" \
              "?wsdl"
service_user = "OdooErp"
service_password = "Joaquin15"


def main():
    client = suds.client.Client(service_url)
    response = client.service.GetCustomerPayments(
        user=service_user,
        password=service_password,
        CreationDateFrom=None,
        CreationDateTo=None,
        CreationTimeFrom=None,
        CreationTimeTo=None,
        Customerid=None,
        PaymentId=None,
        CustomerType=None,
        TypeOfPayment=None,
        ExportMode='C',
        channel=None,
        invoiceId=None)

    if response and response['wsResult']:
        customer_payment_list = response['wsResult']['Payments']['Payment']
        print "Numero de registros:%s" % len(customer_payment_list)
        for customer_payment in customer_payment_list:
            print customer_payment
            print "Tipo: %s Moneda: %s Importe: %s" % (
                customer_payment._Type,
                customer_payment._Currency,
                customer_payment._AmountAppliedToInvoices)


if __name__ == '__main__':
    main()
