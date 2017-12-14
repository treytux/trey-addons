Descripción
===========

Este módulo nos permite asignar características a los productos de la tienda
online sin necesidad de crear variantes tal y como hacen los atributos, con
objeto de poder aplicar filtros en los listados.

Además, las características pueden asignarse a las categorías públicas, para
que únicamente se muestren allí donde tengan sentido.

Ej: En una tienda que se venden ordenadores y consumibles, si estamos mostrando
un listado de cartuchos de tinta no tiene sentido que se puedan aplicar filtros
por Memoria RAM o Tamaño de Disco Duro.

Lógica de Visualización
=======================

Con valores seleccionados de una característica: Se mostrarán aquellos
productos que tengan asignado alguno de los valores.

Con valores seleccionados en más de una característica: Se mostrarán aquellos
productos que tengan asignado al menos un valor de cada una de las
características.

Configuración
==========
- En "Ventas > Configuración > Categorías y atributos de producto
> Características" creamos las características (Ej. Tipo de uso)

Nota: Se incluye un nombre y un nombre público (no obligatorio), con objeto
de que podamos crear 2 características que en la tienda online se llamen igual,
por ejemplo "Fabricante", pero que se vayan a mostrar en categorías diferentes,
por lo que asignaremos al campo nombre "Fabricante Ordenadores" y "Fabricante
Impresoras" y al nombre público simplemente "Fabricante" en ambos casos.

- En "Ventas > Configuración > Categorías y atributos de producto
> Valores de características" creamos los valores para cada característica (Ej.
Interior, Exterior, Ambiente seco) asignando a cada valor su característica
padre

- En "Ventas > Configuración > Categorías y atributos de producto
> Categorías públicas de producto" añadimos a cada categoría aquellas
características que queremos mostrar en la tienda online al visualizar el
listado de productos de dicha categoría

Nota: Si se añade una característica a una categoría, esta no se visualizará
por defecto en todas sus hijas, ya que de esto nos permitirá personalizar
de manera más especifica.

- En "Ventas > Productos > Productos" dentro de la pestaña "Ventas" añadimos a
las plantillas de producto aquellas características y valores que nos
interesen.
