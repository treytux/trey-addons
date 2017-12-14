Account_Analytic_Analysis_Recurring_Extender
=============================================


Caracteristicas añadidas:
---------------------------------
Modifica el comportamiento de la facturacion periodica de contratos y arregla
algunos errores como:
1. La generacion de factura tiene en cuenta la posicion fiscal del cliente.

2. Calcula correctamente los impuestos.

3. Añade un campo descripcion de factura que se llevara como referencia.

4. Añade la posibilidad de usar en la descripcion de factura costantes de:

    * `#MONTH_INT#` =  Añade el mes como entero (01, 02 , 03 )
    * `#MONTH_STR#` =  Añade el mes como texto (enero, febrero, marzo)
    * `#YEAR_INT#`  =  Añade el año como entero (2014, 2015, 2016)
