# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import suds
import log


service_url = "http://booking.methabook.com/wsExportacion/wsCustomers.asmx" \
              "?wsdl"
service_user = "OdooErp"
service_password = "Joaquin2015"


def main():

    _log = log.init_logger('suds.client', debug=True)
    # _log = logging.getLogger('suds.client').setLevel(logging.INFO)
    client = suds.client.Client(service_url)
    response = client.service.getCustomerList(
        user=service_user,
        password=service_password,
        customerType=None,
        creationDateFrom=None,
        creationDateTo=None,
        id=61983,
        ExportMode='C')
    print _log
    if response and response['wsResult']:
        customer_list = response['wsResult']['Customers']['Customer']
        print len(customer_list)
        for customer in customer_list:
            print "Cliente: %s , Canal: %s" % (
                customer.General.Name, customer.General.Channel.value or '')


if __name__ == '__main__':
    main()
