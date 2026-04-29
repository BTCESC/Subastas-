# Archivo de Subastas de Arte

Web privada para registrar, organizar y consultar subastas de cuadros desde móvil u ordenador.

## Objetivo del proyecto

La web funcionará como un archivo personal de obras de arte vistas en subastas. Permitirá guardar información importante de cada cuadro, consultar la colección de forma ordenada y facilitar el registro de nuevas obras mediante lectura automática de fichas con IA.

La idea principal es que el usuario pueda añadir una obra a partir de una ficha de subasta, revisar los datos extraídos y guardar toda la información en una base de datos.

## Qué permitirá hacer la web

La web permitirá registrar cada obra con datos como:

- Imagen del cuadro.
- Imagen o captura de la ficha de subasta.
- Autor.
- Título de la obra.
- Técnica o soporte.
- Medidas.
- Casa de subastas.
- Fecha de la subasta.
- Precio de salida.
- Comisión.
- Precio final calculado.
- Enlace original de la subasta.
- Notas adicionales.

## Zona privada

La web tendrá una zona privada con acceso mediante usuario y contraseña.

Desde esta zona se podrán realizar acciones como:

- Añadir nuevas obras.
- Revisar los datos antes de guardarlos.
- Editar registros ya creados.
- Borrar obras en caso de error.
- Consultar la colección completa.

## Colección de obras

La colección mostrará todas las obras guardadas en formato de listado o tarjetas, con una ficha individual para cada cuadro.

La web estará pensada para consultarse cómodamente desde móvil y ordenador, con un diseño responsive.

## Búsqueda y filtros

La web permitirá localizar obras de forma rápida mediante:

- Búsqueda por autor.
- Búsqueda por título.
- Búsqueda por casa de subastas.
- Filtro por técnica.
- Filtro por fecha.
- Filtro por precio.
- Filtro por casa de subastas.

El objetivo es que la colección no sea solo un listado, sino una herramienta útil para comparar y encontrar obras rápidamente.

## Lectura de fichas con IA

Una función importante será la lectura automática de fichas mediante IA.

El usuario podrá subir una imagen o captura de la ficha de subasta y la web intentará extraer automáticamente datos como:

- Autor.
- Título.
- Técnica.
- Precio.
- Medidas.
- Número de lote, si aparece.

Antes de guardar la obra, el usuario podrá revisar y corregir manualmente los datos extraídos.

## Cálculos útiles

La web también calculará datos útiles para comparar obras, como:

- Precio final con comisión incluida.
- Superficie de la obra en cm².
- Ratio de precio por cm².

Esto permitirá comparar mejor unas obras con otras, incluso cuando tengan tamaños o precios diferentes.

## Control de autores

Uno de los problemas que se quiere evitar es que un mismo autor aparezca duplicado por diferencias en el nombre.

Por ejemplo:

- Picasso
- Pablo Picasso
- Pablo Ruiz Picasso

La web deberá intentar agrupar correctamente estos casos, permitiendo usar un autor ya existente o crear uno nuevo cuando se registre una obra.

Más adelante se podrá añadir una función para fusionar autores duplicados.

## Tecnologías previstas

La versión inicial se plantea como una web hecha con:

- Python.
- Flask.
- HTML.
- CSS.
- Base de datos.
- Subida de imágenes.
- Integración futura con IA para lectura de fichas.

## Estado actual

Proyecto en fase inicial.

Primera fase:

- Estructura base del proyecto.
- Portada.
- Página inicial de colección.
- Diseño responsive básico.
