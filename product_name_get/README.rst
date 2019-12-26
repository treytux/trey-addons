.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Product name get
====

Permite definir un patrón del nombre a mostrar de plantilla y variante de
producto por separado.
Si el patrón contiene nombres de campo erróneos se devolverá el valor por
defecto y se mostrará un error en el log para informar.

Configuración
----
Desde el menú Ajustes/Técnico/Parámetros/Parámetros del sistema se puede
modificar el valor para las claves:

    - product_name_get.product_product_name_pattern

    - product_name_get.product_template_name_pattern

teniendo en cuenta que cada campo que se quiera mostrar debe ir precedido de
"%(" y finalizar con ")s".
