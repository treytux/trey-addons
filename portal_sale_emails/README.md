Portal Sale Emails
==================

Sobrescribe las plantillas de correo electrónico que se utilizan para las
notificaciones de Pedido y Factura.

> Nota: Este módulo **no ha de instalarse directamente** en producción.
> Consultar el apartado Cómo se usa.

Cómo se usa
-----------

Copiar el fichero "/data/portal_sale_data.xml" en nuestro módulo y realizar
las modificaciones necesarias para la personalización.

En el fichero `__openerp__.py` añadimos las dependencias (si no lo estaban ya)
e incluimos el fichero que contiene las plantillas `data/portal_sale_data.xml`.

```xml
'depends': [
    'portal_sale',
],
'data': [
    'data/portal_sale_data.xml',
],
```

> Nota: Por defecto los ficheros de datos no se actualizan una vez instalados
> para permitir que el cliente pueda modificar la plantilla desde el ERP. En
> caso de que queramos que se comporte de forma diferente establecer el
> atributo `noupdate="0"` del fichero `portal_sale_data.xml`.

```xml
<data noupdate="0">
```
