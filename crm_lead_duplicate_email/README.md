
crm_lead_duplicate_email
========================


#### Funcionalidad

Cuando tenemos instalado el modulo de CRM desde la ventana de oportunidades
podemos seleccionar varias oportunidades y enviar un correo electronico.

El problema es que si hemos asignado en varias oportunidades un mismo contacto
o una misma direccion de correo, envia varias correos en funcion de los registro
seleccionados en los que se incluya este partner o direccion de correo.


#### Uso

El modulo modifica el wizard de envio de correo desde oportunidades, recorriendo
los registros seleccionados. Se crea una lista con los id de los partner de forma
unica y se filtran los registros activos para enviar al compositor de correos para
que solo envie un correo por partner o direccion de correo.





