.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======
Edifact
=======


Base module for import / export edifact desadv files.

Dependecies
-----------

Bots:

http://bots.readthedocs.io/en/latest/installation/


#install django

$ wget -O django.tar.gz https://www.djangoproject.com/download/1.4.13/tarball/

$ tar -xf django.tar.gz

$ cd Django-1.4.13

$ sudo python setup.py install

$ cd ..

#install cherrypy

$ wget http://download.cherrypy.org/CherryPy/3.2.2/CherryPy-3.2.2.tar.gz

$ tar -xf CherryPy-3.2.2.tar.gz

$ cd CherryPy-3.2.2

$ sudo python setup.py install

$ cd ..
#install Genshi

$ wget http://ftp.edgewall.com/pub/genshi/Genshi-0.7.tar.gz

$ tar -xf Genshi-0.7.tar.gz

$ cd Genshi-0.7

$ sudo python setup.py install

$ cd ..
#install bots

$ wget -O bots-3.1.0.tar.gz https://sourceforge.net/projects/bots/files/bots%20open%20source%20edi%20software/old%20releases/bots3.1.0/bots-3.1.0.tar.gz/download

$ tar -xf bots-3.1.0.tar.gz

$ cd bots-3.1.0

$ sudo python setup.py install

$ cd ..
#set rigths for bots directory to non-root:

$ sudo chown -R myusername /usr/lib/python2.6/site-packages/bots

#start up bots-webserver:

$ bots-webserver.py


Configuration parameters:
=========================


Configuration > Companies > Companies > Configuration > EDI parameters

Salesman: sales person for documents

In path: path for import files

Out path: path for exported files

Paths indiqued here must exist in your server.

