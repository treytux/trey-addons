Analityc_Account_Analysis_Lisprice_Per_Company
=============================================


Caracteristicas:
---------------------------------

Si tenemos instalado el modulo sale_listprice_per_company que convierte el 
campo list_price del objeto product.template a un campo company depend, hay 
modulos que realizan consultas directas a la base de datos buscando este campo.

Uno de los modulos afectados es analytic_account_analysis.
Este modulo modifica dichas consultas SQL para extraer el valor de campo 
list_price de la tabla ir_property
