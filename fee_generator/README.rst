.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============
Fee generator
=============

Este módulo permite gestionar cuotas para cualquier modelo y recurso.

Se puede acceder a las cuotas de forma genérica desde el menú de Contabilidad > Clientes > Generador de cuotas.


Módulo de enlace
================

Es necesario el desarollo de un módulo que sirva de enlace entre el modelo origen y el generador de cuotas. Deberá incluirse en el módulo de enlace un campo que haga referencia al generador de cuotas e incluir en la vista el campo de la siguiente forma:

<field name="fee_generator_id" context="{'default_partner_id': partner_id, 'default_model_name': 'model.name', 'default_res_id':id}"/>

En el contexto se le pasa la información necesaria para vincular el partner al que se facturará (partner_id), el modelo origen (model_name) y el id del recurso origen (res_id). Con esta información, la factura mostrará como descripción y documento origen el nombre del recurso origen.


Estados y campos
================

.. image:: fee_generator/static/description/fee_generator.png

Los posibles estados del generador de cuotas serán:
Borrador > Activo > Finalizado o Cancelado.

Entre sus campos, se cuentran los siguientes:
- Cliente: se carga automáticamente si viene del contexto anteriormente explicado.
- Producto cuota: servirá para aplicar los impuestos a las facturas generadas.
- Referencia de factura: será la referencia de la factura y la descripción que se aplique a la línea de factura que se creará.
Se pueden aplicar los siguientes patrones:
#MONTH_INT# : mostrará el número del mes. Ej: "Cuota #MONTH_INT#" se traducirá por "Cuota 05" si el mes de la próxima fecha es mayo.
#MONTH_STR# mostrará el nombre del mes.
#YEAR_INT#: mostrará el número de año.
- Descripción: descripción para la línea de factura.
- Diario: el diario que aparecerá en las fecturas generadas.
- Total sin impuestos: total a cobrar sin impuestos, a repartir entre las cuotas.
- Descuento: descuento que se aplicará al total sin impuestos.
- Cuotas totales: número de cuotas en las que se pagará el importe total.
- Cantidad cuota sin impuestos: es un campo que se calcula como:
    importe total / número de cuotas


Generación de facturas
======================

Desde el generador se puede crear una nueva factura pulsando sobre "Próxima factura", siempre y cuando el pendiente sin impuestos sea distinto de cero y el estado sea "Activo". La fecha de la factura será la correspondiente a la "Próxima fecha" antes de generar la factura. Una vez generada, la próxima fecha se actualizará según el periodo de repetición indicado en "Repetir cada".

Si no desea llevar manualmente las generación de las facturas, se pueden gestionar automáticamente haciendo uso del planificador "Generate pending fees", instalado con este mismo módulo. Para poder ver el planificador, es necesario que el usuario tenga permisos de "Características técnicas". Se puede encontrar en:

* Configuración > Técnico > Automatización > Acciones planificadas

Este planificador revisa la "Próxima fecha" de todos los generadores de cuotas y si el importe pendiente sin impuestos es mayor que cero. Si la fecha de próxima factura es igual o menor a hoy y aún queda importe pendiente, genera la factura correspondiente y actualiza la próxima fecha de la misma forma que la generación manual.

Si una factura se cancela, el importe pendiente sin impuestos se actualizará indicando que quedan facturas por generar.

Las facturas generadas aparecerán en "Facturas generadas", y podrán abrirse pulsando sobre el icono del archivador de la lista.



