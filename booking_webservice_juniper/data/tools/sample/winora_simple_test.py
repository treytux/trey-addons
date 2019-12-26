# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import requests
import xml.etree.ElementTree as eTree
from xml.etree.ElementTree import fromstring
import xml
from tempfile import NamedTemporaryFile
import lxml

service_url = "http://b2b.bike-parts.de/xml/"
service_user = "81602736"
service_password = "33bimbdg"


def main():
    fileobj = NamedTemporaryFile('w+', suffix='.xml')
    s = requests.session()
    s.verify = False
    s.auth = (service_user, service_password)
    resp = s.get(service_url, params={'loginid': service_user,
                                      'password': service_password,
                                      'processtype': 'searchcatalog',
                                      'searchpattern': '*',
                                      'pagesize': '10&page=80'}, stream=True)
    content = resp.text.encode('ISO-8859-1')
    parser = eTree.XMLParser(encoding='ISO-8859-1')
    tree = fromstring(content, parser=parser)
    root = xml.etree.ElementTree.Element("products")
    items = tree.findall("item")
    for item in items:
        root.append(item)
    xml.etree.ElementTree.ElementTree(root).write(fileobj, 'ISO-8859-1')
    pepe = lxml.etree.parse(content)
    print pepe
    print content


if __name__ == '__main__':
    main()
