# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import suds


service_url = "http://booking.methabook.com/wsExportacion/wsSuppliers.asmx" \
              "?wsdl"
service_user = "OdooErp"
service_password = "Joaquin2015"


def main():
    client = suds.client.Client(service_url)
    response = client.service.getSupplierList(
        user=service_user,
        password=service_password,
        SupplierId=441,
        ExportMode='C')
    if response and response['wsResult']:
        supplier_list = response['wsResult']['Suppliers']['Supplier']
        print len(supplier_list)
        for supplier in supplier_list:
            print "Proveedor: %s , Canal: %s" % (
                supplier.General.Name, supplier.General.Channel.value or '')


if __name__ == '__main__':
    main()
