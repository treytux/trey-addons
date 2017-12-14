Información
===========

Smart Search. This module provide smart search on
eCommerce.

Instalación
===========
Se tienen las siguientes dependencias:

```
```

Configuración
=============
- Tiempo de caché (Tiempo máximo para que se regeneré la caché)
- Minimo numero de palabras para que se inicia la busqueda

Blueprint / Roadmap
===================
- [COMPROBAR ORDENACIÓN] Añadir campo secuencia y su widget en la vista a los productos del histórico
- Revisar por que no aparece en la vista de los banners el campo name como traducible
- Revisar en que orden aparecen las categorías en los resultados (¿cual deberían tener?: más productos, alfabético, el mismo que los productos)
- Si mostramos n productos junto a la categoría, ¿deberíamos filtrar el listado después de hacer clic con los ids de dichos productos?
  HECHO
- ¿Cuando se calcula el contador de búsquedas y de hits (clics)?
  HECHO
- Revisar error al crear/modificar cache
  File "/home/jcamacho/workspace/odoo/instances/trey/addons/website_sale_search_suggestions/controllers/main.py", line 114, in search
    'last_cache_update': fields.Datetime.now()})
  File "/home/jcamacho/workspace/odoo/server/openerp/workflow/helpers.py", line 6, in __init__
    assert isinstance(uid, (int, long))
AssertionError
  HECHO
- Reemplazar el número de resultados fijo por uno dinámico del controlador en los resultados de la web
  HECHO
- Revisar opción Configuración del menú Search Suggestions
  HECHO
- Revisar Aplicar y Cancelar de la opción Configuración del menú Search Suggestions
  HECHO
- Almacenar las búsquedas realizadas en un modelo de datos 'search_history'
     - Campos
         - name: que contendrá la cadena buscada
         - result_product_ids: relación con los productos encontrados
         - searches: Número de veces buscada la cadena
         - clicks: Número de veces que se hizo clic en un resultado
    en caso de que exista una entrada en cache y la diferencia de tiempo desde su ultima
    actualizacion hasta este moemnto es menor a un umbral se devuelven los datos de cache
    en caso contrario(se supera el umbral) se regeneran los valores para esa entrada
    en el modelo.
    En el caso de que no exista una entrada se genera y se le asignan los valores de los
    productos y categorias que ha devuelto.

  HECHO
- Inclusión de las categorias antes que los productos en los resultados de
  busqueda.
    creo nueva funcion en javascript Suggestion item category y un nuevo template
    antes de las categorias hacer lo mismo con el banner

  HECHO
- Incluir un tiempo minimo para generar una peticion ayax despues de escribir
      un texto en el input.

  HECHO
- Banner informativo imagen del producto que se busca

  HECHO
- tiempo para regenerar la cache. Chequeamos el tiempo de la cache y si a
  pasado x tiempo desde la ultima actualizacion la generamos.
      Igual que google shopping
      Incluimos variable en modelo. comparamos el tiempo en que se regenero
      por ultima vez y si el tiempo se a excedido se regeneran los valores
      en caso de no existir la busqueda se crea

  HECHO
- Añadir a configuracion los siguentes campos:
    product_name_score
    product_description_score
    product_sale_description_score
    product_default_code_score

  ANULADO
- Añadir un campo en la configuración del Website para fijar el número de
  caracteres de corte para facilitar resultados. Defecto 3 caracteres.

  SOLUCIONADO CON LOS TERMS------------------------------------------SYNONYMOUS
- Corregir palabras se hara desde synonimous caracteres de corte para facilitar
  resultados. Defecto 3 caracteres.

  HECHO
- Controlar el tiempo desde la ultima tecla que se ha pulsado para enviar la
  petición al servidor. Tiempo entre dos teclas(para 5 caracteres hace 3
  busquedas para reducir las peticiones al servidor)

- Incluir un rating (o peso) para los productos y que se orden segun este.

- Colocar manualmente la prioridad de los resultados de una busqueda.
  (https://swiftype.com/site-search)


