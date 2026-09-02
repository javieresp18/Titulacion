# Bitacora de decisiones metodologicas operativas

Registra las decisiones tecnicas necesarias para ejecutar la metodologia cuando el documento de titulacion no fija un detalle computacional literal (apartado 6 del protocolo de ejecucion).

## 3.6 / 3.10

- **Evidencia en Data-set.xlsx:** Distribucion de ClasificacionDiferenciaMonetaria: {'Coincidencia exacta': 15716, 'No evaluable': 5450, 'Diferencia material': 427, 'Diferencia menor': 53, 'Posible error': 8, 'Diferencia de redondeo': 6}
- **Decision operativa:** Se mantiene SubTotal como variable monetaria principal (no se sustituye por CostoCalculado).
- **Justificacion:** El documento de titulacion establece SubTotal como variable monetaria principal salvo evidencia concluyente en contra; no se hallo tal evidencia.
- **Impacto esperado:** Ninguno sobre la variable objetivo; CostoCalculado se usa solo como control de calidad.

## 3.4 (categorias tecnicas)

- **Evidencia en Data-set.xlsx:** Categoria 'ACEITE': 490 registros, 617983.51 USD (2.75% del costo bruto por categoria).
- **Decision operativa:** INCLUIDA
- **Justificacion:** Decision operativa conservadora: sin evidencia de pertenecer a categorias explicitamente excluidas, se mantiene en el analisis agregado (ver bitacora_decisiones_metodologicas.md).
- **Impacto esperado:** Material

## 3.4 (categorias tecnicas)

- **Evidencia en Data-set.xlsx:** Categoria 'FERRETERIA': 8591 registros, 1935083.87 USD (8.62% del costo bruto por categoria).
- **Decision operativa:** INCLUIDA
- **Justificacion:** Categoria listada explicitamente en el apartado 3.4 como pertinente al mantenimiento naval.
- **Impacto esperado:** Material

## 3.4 (categorias tecnicas)

- **Evidencia en Data-set.xlsx:** Categoria 'FILTROS': 473 registros, 198637.99 USD (0.88% del costo bruto por categoria).
- **Decision operativa:** INCLUIDA
- **Justificacion:** Categoria listada explicitamente en el apartado 3.4 como pertinente al mantenimiento naval.
- **Impacto esperado:** Marginal

## 3.4 (categorias tecnicas)

- **Evidencia en Data-set.xlsx:** Categoria 'GRASAS': 12 registros, 1609.85 USD (0.01% del costo bruto por categoria).
- **Decision operativa:** INCLUIDA
- **Justificacion:** Decision operativa: funcionalmente equivalente a ACEITES/lubricacion de maquinaria, dentro del alcance de mantenimiento tecnico (ver bitacora_decisiones_metodologicas.md).
- **Impacto esperado:** Marginal

## 3.4 (categorias tecnicas)

- **Evidencia en Data-set.xlsx:** Categoria 'MATERIALES DE LIMPIEZA': 977 registros, 77576.83 USD (0.35% del costo bruto por categoria).
- **Decision operativa:** EXCLUIDA
- **Justificacion:** Decision operativa: insumo ajeno al mantenimiento tecnico naval, analogo a las categorias excluidas literalmente (ver bitacora_decisiones_metodologicas.md).
- **Impacto esperado:** Marginal

## 3.4 (categorias tecnicas)

- **Evidencia en Data-set.xlsx:** Categoria 'PINTURAS': 1660 registros, 843469.93 USD (3.76% del costo bruto por categoria).
- **Decision operativa:** EXCLUIDA
- **Justificacion:** Categoria listada explicitamente en el apartado 3.4 como ajena al mantenimiento naval (insumo de hotelera, oficina, salud o seguridad).
- **Impacto esperado:** Material

## 3.4 (categorias tecnicas)

- **Evidencia en Data-set.xlsx:** Categoria 'QUIMICOS': 542 registros, 178988.84 USD (0.80% del costo bruto por categoria).
- **Decision operativa:** INCLUIDA
- **Justificacion:** Categoria listada explicitamente en el apartado 3.4 como pertinente al mantenimiento naval.
- **Impacto esperado:** Marginal

## 3.4 (categorias tecnicas)

- **Evidencia en Data-set.xlsx:** Categoria 'REPUESTOS ELECTRICOS': 215 registros, 192425.72 USD (0.86% del costo bruto por categoria).
- **Decision operativa:** INCLUIDA
- **Justificacion:** Decision operativa conservadora: sin evidencia de pertenecer a categorias explicitamente excluidas, se mantiene en el analisis agregado (ver bitacora_decisiones_metodologicas.md).
- **Impacto esperado:** Marginal

## 3.4 (categorias tecnicas)

- **Evidencia en Data-set.xlsx:** Categoria 'REPUESTOS MECANICOS': 3462 registros, 4893371.10 USD (21.80% del costo bruto por categoria).
- **Decision operativa:** INCLUIDA
- **Justificacion:** Decision operativa conservadora: sin evidencia de pertenecer a categorias explicitamente excluidas, se mantiene en el analisis agregado (ver bitacora_decisiones_metodologicas.md).
- **Impacto esperado:** Material

## 3.4 (categorias tecnicas)

- **Evidencia en Data-set.xlsx:** Categoria 'SERVICIOS DE MANTENIMIENTO': 5238 registros, 13508551.90 USD (60.18% del costo bruto por categoria).
- **Decision operativa:** INCLUIDA
- **Justificacion:** Categoria listada explicitamente en el apartado 3.4 como pertinente al mantenimiento naval.
- **Impacto esperado:** Material

