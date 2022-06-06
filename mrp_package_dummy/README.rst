.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Mrp package dummy
===================

Con este módulo se pueden generar etiquetas tontas (sin información) para que
sean peagadas en los paquetes para su posterior registro.

El funcionamiento es el siguiente:
- Se imprime las etiquetas dummy.
  En la etiequeta se puede definir un producto, empaquetado y unidades por paquete.
  Del empaquetado se imprimirá el DUN14.
- Desde un asistente de lectura se puede disparar a eiquetas y se crearán paquetes
  con la información con la que fueron creadas.

Hay otro modulo mrp_package_dummy que permite disparar a estas etiquetas desde
la finalización de una fabricación de esta forma se generan los paquetes en el sistema.

Configuracion
Existen dos parametros del sistema:
- stock_package_dummy.prefix (valor por defecto "000000000"): corresponde al prefijo del codigo de barras
