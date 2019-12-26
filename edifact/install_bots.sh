##############################################################################
#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################

#install django
mkdir bots
cd bots_requirements

wget -O django.tar.gz https://www.djangoproject.com/download/1.4.13/tarball/

tar -xf django.tar.gz
cd Django-1.4.13
sudo python setup.py install
cd ..

#install cherrypy
wget http://download.cherrypy.org/CherryPy/3.2.2/CherryPy-3.2.2.tar.gz
tar -xf CherryPy-3.2.2.tar.gz
cd CherryPy-3.2.2
sudo python setup.py install
cd ..

#install Genshi
wget http://ftp.edgewall.com/pub/genshi/Genshi-0.7.tar.gz
tar -xf Genshi-0.7.tar.gz
cd Genshi-0.7
sudo python setup.py install
cd ..

#install bots
tar -xf bots-3.1.0.tar.gz
cd bots-3.1.0
sudo python setup.py install
cd ..

#set rigths for bots directory to non-root:
sudo chown -R $USER /usr/lib/python2.7/site-packages/bots
sudo chown -R $USER /usr/local/lib/python2.7/dist-packages/bots

