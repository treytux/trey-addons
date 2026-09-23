Contract Lite Line Server
=========================

Este módulo añade información de servidor administrado a las líneas de
contratos ligeros.

Permite marcar productos de servicio como servidor, registrar el servidor y
contenedor asociado a una línea de contrato, controlar espacio contratado y
consumido en GB, y actualizar la ocupación consumida desde la salida de una
herramienta externa.

Funcionalidades
---------------

* Añade el campo ``Es servidor`` en productos de servicio.
* Muestra un bloque de servidor administrado en las líneas de contrato cuyo
  producto esté marcado como servidor.
* Registra servidor, contenedor, espacio contratado, espacio consumido, línea
  de ampliación de disco, espacio ampliado y saldo actual.
* Calcula una ampliación sugerida proyectando el crecimiento histórico a seis
  meses y aplicando un buffer de seguridad.
* Permite importar ocupación para los contratos seleccionados.
* Añade un filtro de líneas con saldo de servidor negativo.
* Permite notificar por correo a los seguidores del cliente comercial y del
  contrato, dejando traza en el chatter del contrato.

Uso
---

Desde el listado de contratos se puede abrir el asistente de importación,
pegar la salida de ocupación, revisar el log de contenedores encontrados y
aplicar los cambios. Desde el listado de líneas de contrato se pueden filtrar
las líneas de servidor con saldo negativo y lanzar la notificación de uso de
espacio.

La plantilla de correo de notificación es editable desde el backend y se usa
para generar tanto la traza en el chatter del contrato como las notificaciones
a los seguidores, renderizándose en el idioma correspondiente.
