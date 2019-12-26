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
    response = client.service.GetBankAccounts(
        user=service_user,
        password=service_password,
        id=None,
        AccountType=None,
        ExportMode='C')
    if response and response['wsResult']:
        bank_list = response['wsResult']['BankAccs']['BankAcc']
        print "Numero de registros:%s" % len(bank_list)
        for bankacc in bank_list:
            print "Cuenta: %s , Referencia: %s" % (
                bankacc.Name, bankacc.AccountRefNumber or '')


if __name__ == '__main__':
    main()
