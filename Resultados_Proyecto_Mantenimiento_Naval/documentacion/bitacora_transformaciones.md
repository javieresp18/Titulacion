# Bitacora de transformaciones aplicadas al dataset

Fuente: Data-set.xlsx. Cada paso sigue el orden establecido en el apartado 3.6 de la metodologia.

- Conversion de tipos: FechaCont a datetime; columnas monetarias y Quantity a float64.
- Validacion de fechas: 0 registros con FechaCont invalida o no convertible.
- Normalizacion de texto: mayusculas, recorte de espacios y colapso de espacios multiples en variables categoricas y descriptivas.
- Duplicados exactos detectados (todas las columnas originales): 250 registros (572378.23 USD), excluidos en el escenario principal.
- Posibles duplicados logicos (coincidencia parcial, sin ser duplicado exacto): 298 registros. No se eliminan sin evidencia adicional.
- Anulaciones contables: no se identificaron pares de anulacion verificables (montos negativos con contraparte positiva exacta del mismo ItemCode y Cardcode).
- Validacion codigo-descripcion: 4721 de 5291 ItemCode con correspondencia verificable para el nivel individual; los codigos ambiguos permanecen en el costo agregado.

## Conciliacion de filas

|   FilasOriginales |   DuplicadosExcluidos |   AnulacionesVerificadas |   CategoriasExcluidas |   OtrasExclusionesJustificadas |   FilasDepuradas |
|------------------:|----------------------:|-------------------------:|----------------------:|-------------------------------:|-----------------:|
|             21660 |                   250 |                        0 |                  2631 |                              0 |            18779 |

## Conciliacion de costos (USD)

|   CostoBrutoUSD |   CostoDuplicadosExcluidosUSD |   EfectoAnulacionesUSD |   CostoCategoriasExcluidasUSD |   EfectoOtrasExclusionesUSD |   CostoDepuradoUSD |   CostoDepuradoCalculadoUSD |
|----------------:|------------------------------:|-----------------------:|------------------------------:|----------------------------:|-------------------:|----------------------------:|
|     2.24477e+07 |                        572378 |                      0 |                        920774 |                           0 |        2.09545e+07 |                 2.09545e+07 |

## Sensibilidad: duplicados excluidos vs conservados

- escenario_principal_filas: 18779
- escenario_principal_costo_usd: 20954546.84
- escenario_alternativo_conservando_duplicados_filas: 19029
- escenario_alternativo_conservando_duplicados_costo_usd: 21526925.07
