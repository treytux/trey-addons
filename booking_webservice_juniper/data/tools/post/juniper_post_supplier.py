# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import requests

service_url = ("http://booking.methabook.com/wsExportacion/wsSuppliers.asmx"
               "/getSupplierList")
service_user = "OdooErp"
service_password = "Joaquin15"


def main():
    # fileobj = NamedTemporaryFile('w+', suffix='.xml')
    s = requests.session()
    s.verify = False
    # s.auth = (service_user, service_password)
    # resp = s.get(service_url, params={'user': service_user,
    #                                   'password': service_password,
    #                                   'SupplierId': 'searchcatalog',
    #                                   'ExportMode': 'C'}, stream=True)

    resp = requests.post(service_url, data={
        'user': service_user,
        'password': service_password,
        'SupplierId': '438',
        'ExportMode': 'C'})

    print resp.text

    # content = resp.text.encode('ISO-8859-1')
    # parser = eTree.XMLParser(encoding='ISO-8859-1')
    # tree = fromstring(content, parser=parser)
    # root = xml.etree.ElementTree.Element("products")
    # items = tree.findall("item")
    # for item in items:
    #     root.append(item)
    # xml.etree.ElementTree.ElementTree(root).write(fileobj, 'ISO-8859-1')
    # pepe = lxml.etree.parse(content)
    # print pepe
    # tree = xml.etree.ElementTree.ElementTree(root)
    # tree.write(fileobj, 'ISO-8859-1')
#        print item.find("description1").text, item.find(
#            "description2").text, item.find("unitprice").text, item.find(
#            "availablestatus").text

#        root.append(item)
    # fromstring.Element("item").write(fileobj, 'ISO-8859-1')
    # print content


if __name__ == '__main__':
    main()
