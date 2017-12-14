# Modulo para la importancion estandar de datos a Odoo

## Introduccion
Buscando una forma de poder estandarizar la importacion de datos para las 
nuevas implantaciones de odoo, hemos buscando un sistema basado en 
plantillas excel o calc. La idea es separa la parte de importacion de la 
parte de extraccion para poder estandarizar procesos.

Si separamos la parte de importacion, podemos proveer a los clientes de 
plantillas para que sean ellos los que extraigan los datos de su sistema y 
no las den rellenas para su importacion.
Esto hace que podamos fijar un precio para una importacion estandar en la 
que el cliente nos da todos



## Caracteristicas
Se basa en el trabajo realizado por Roberto en el modulo OdooCli y utiliza 
ficheros csv basados en las plantillas excel o calc exportados a csv.

Con un proceso ETL de Pentaho, vuelco a fichero csv en el formato que espera
 el toolkit para la importacion. Esta pendiente hacer este proceso de 
 conversion directamente desde python.
 
 
###Carpeta tools
Contiene los distintos ficheros python para la carga de los registros 
contenidos en la carpeta data con los nombre especificos.

###Carpeta kettle
 Contiene las transformaciones y trabajos de Pentaho Kettle para convertir 
 las plantillas excel u openoffice a ficheros CSV delimitados, con 
 codificacion UTF-8 y mapeando los nombre de columna de las hojas a sus 
 correspondientes campos de odoo.

###Carpeta odoocli
 Enlace simbolico al modulo odoocli desarrollado por Roberto.
 

## ToDO
[] Scripts de importacion por bloques.

[] Scripts para la generacion de los csv desde python.

[] Modulo para odoo que ejecute la importacion y almacene los log.
