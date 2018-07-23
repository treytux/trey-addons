
partner_contact_role
====================


#### Funcionalidad

Para los contactos de un partner, se asigna un rol para especifica que
tipos de correo electronico va a recibir. Se utiliza para definir que contactos
reciben los pedidos de venta, facturas, ofertas, etc.

Al ejecutar los asistentes para enviar un pedido de venta, una factura, etc
el sistema tiene comprueba si hay un rol definido para ese objeto y de ser asi, solo nos muestra
los contactos que cumplan con ese rol.
De no encontrarse ningun contacto, nos filtra para mostrarnos el partner y sus contactos.


#### Objetos

Se crea un objeto _**ResPartnerRole**_ en el que se define un nombre para el rol
y el modelo relacionado con ese rol (sale.order, account.invoice, etc)


#### Uso

En el menu de ventas, libreta de direcciones, role, definimos los roles
a asignar a los contactos.

Desde la ficha de partner, al crear un contacto nuevo, a continuacion del tipo
de direccion podemos especificar el rol para dicho contacto.






