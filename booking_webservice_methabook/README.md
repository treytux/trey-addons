Booking Webservice Methabook
============================

# WebService:


Son 4 funciones a implementar que iran asociados a un cron:

  1. Procesar JSON de con todas las reservas tras GET a la api
  2. PUT a la api con de las reservas, customer y suppliers procesados.
  3. PUT para marcar reservas como pagadas.
  4. PUT para indicar si el cliente tiene credito o no. (Controlar segun las fechas del ultimo barrido realizado y filtrar por todos los clientes con cambios en el campo credit).


1. ***Procesado de JSON:***
- endpoint: erpapi.iboosy.com/export
Recorremos el json de forma unidireccional para procesar los bookings que a priori tengan estos dos campos.
Cada "booking del json" corresponde al objeto booking
~~~
    Crear/actualizar ==> Crear/actualizar ==>   Crear/Actualizar solo reservas
        customer                suplier            con Customer y supplier
            |                      |               no incluidos en listas de
            |                      |                      no validos
            *                      *
        Generar lista        Generar lista
        de no validos        de no validos
~~~
2. ***Put a la api con las reservas, customer y suppliers procesados.***
- endpoint: erpapi.iboosy.com/export/confirm

~~~
{
  "exportId": "f4922009-51ba-4ea3-b71f-dc6c5a627079",
  "exportedAt": "2017/06/01 15:32",
  "customers": [
    {
      "account": "4300000058"
    }
  ],
  "suppliers": [
    {
      "account": "4300000058"
    }
  ],
  "bookings": [
    {
      "locator": "4300000058"
    },
    {
      "locator": "LOCXXXXX"
    }
  ]
}
~~~

3. ***Marcar Reserva como pagada***
- endpoint: erpapi.iboosy.com/booking/paid
~~~
{
  "bookings": [
    {
      "locator": "LOC00012"
    },
    {
      "locator": "LOC00013"
    }
  ]
}
~~~



4. ***Actualizar Credito del cliente:***
- endpoint: erpapi.iboosy.com/customer/changecredit
~~~
{
  "Account":”4300000058”,
  “WithCredit”: true
}
~~~
Casuisticas:
- No tiene saldo, limite_research = True (ya se se ha detectado, vuelve a no tener saldo)
    - si han pasado los dias indicados en la compañia, _days_to_notify_customer_: notifica de nuevo

- No tiene saldo, _credit_limit_reached = False_ (Nuevo con sin saldo)
    - _credit_limit_reached = True_
    - anotamos fecha
    - notificamos api

- Tiene saldo, _credit_limit_reached = True_ (viene de estar sin saldo, NUEVAmente con saldo)
    - notificamos tiene saldo:
    - notificamos api

- Tiene saldo, _credit_limit_reached = False_ (situacion normal)
  - tiene un 80% ?
  - notificariamos



# Vistas Webservice:
Menu Reservas/ Configuración / Webservice:
Existe un webservice para cada acción:
  - Solole booking: Proceso principal de importación de reservas.
  - Solole Confirm Booking: Tras el procesamiento de las reservas se indican las reservas, los clientes y los proveedores importados en Odoo.
  - Solole Paid: Webservice para indicar a la plataforma de iboosy que queda pagada esa reserva.
  - Solole Change credit: Websevice para indicar si tiene saldo o no el cliente.

# Tests:
En el directorio test hay tres ficheros:
  + El servidor: levanta el "servicio" de la api.

  + api.py: para las pruebas de la estructura del JSON.
  + test_webservice_methabook.py : para lanzar el procesado de las reservas

Para realizar las pruebas de **conexión**:
  + Podemos lanzar el servidor Fake en el propio directorio de tests y nos proporciona la "api" con dos rutas para realizar los GET de exportación de reservas:
  ``` 
    $ python web-server_api.py
  ```
 
  + http://localhost:8080/
       nos da un json con los datos que nos proporciono iboosy al principio.
      contienen datos insuficiones en campos de customer,booking,suppliers.
  + http://localhost:8080/content2
      nos da un json con datos reales, pero faltan Zones, para componer el lugar de la reserva.

  + Siempre tener en cuenta la convivencia de los dos webservice: type=juniper y type=methabook

__Para realizar las pruebas de carga de datos__:
  + Descomentamos el boton:
    + 'First Load Bookings Json' situado en *booking_webservice_methabook/views/webservice_view.xml*.
  + Desde Odoo, en apartado Reservas, apartado Webservice Log, vamos a copiar el json que produce el error:
    * Filtramos por Tipo: reserva, Estado: bookings
    * Seleccionamos la ultima importación. Pestaña Datos importados y copiamos el contenido entre corchetes para pegarlo en un fichero ubicado en tests para realizar su carga manual.
  + En la función **first_load_bookings_json** (*trey-addons/booking_webservice_methabook/models/webservice.py*) indicamos el fichero test a cargar y podemos empezar a importar reservas desde el fichero.
  
