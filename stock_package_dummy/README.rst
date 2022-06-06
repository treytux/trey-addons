.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock package dummy
===================

Con este modulo se pueden generar etiquetas tontas (sin información) para que
sean pegadas en los paquetes para su posterior registro.

El funcionamiento es el siguiente:
- Se imprimen las etiquetas dummy.
  En la etiequeta se puede definir un producto, empaquetado y unidades por paquete.
  Del empaquetado se imprimirá el DUN14.
- Desde un asistente de lectura se pueden disparar las etiquetas y se crearán paquetes
  con la información con la que fueron creadas.

Hay otro módulo mrp_package_dummy que permite disparar a estas etiquetas desde
la finalización de una fabricación de esta forma se generan los paquetes en el sistema.

