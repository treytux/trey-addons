=================
Sale Session
=================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo evita que el campo sesión de ventas se rellene automáticamente en los usuarios que tienen activa la opción "Campo Sesión vacío en Ventas"

**Tabla de contenidos**

.. contents::
   :local:

Uso
===

#. Ir a *Configuración > Ajustes > Usuarios y compañías>Usuarios>Elige el usuario*.
#. En el menú de configuración técnica.
#. Activar o desactivar el campo Campo Sesión vacío en Ventas.

Instrucciones de actualización
===============================

Actualización 1.5.0 a 1.6.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Si tenemos el modelo 347 instalado en el sistema con declaraciones creadas. Nos dara un error al intentar pasar la
factura a borrador. Lo ideal es borrar esas declaraciones y si es necesario volver a crearlas porque aunque las pasemos
a borrador no elimina las lineas antes calculadas.
#. Si tenemos cobros y hay establecida una fecha de corte de contabilidad posterior a la esta fecha, nos dara un error
porque no puede cancelar el asiento. Una opcion es cambiar la fecha de bloqueo antes de actualizar y volver a
establecerla una vez este actualizado


Créditos
========

Autor
~~~~~

* `Trey <https://www.trey.es>`__:
