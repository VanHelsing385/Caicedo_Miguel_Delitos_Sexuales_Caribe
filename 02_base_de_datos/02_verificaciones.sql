-- =====================================================================
-- Consultas de comprobacion de la carga (editor SQL de Neon)
-- Cada una indica el resultado esperado. Si alguna no coincide, la carga
-- no se da por buena.
-- =====================================================================

-- V1. Filas por tabla (esperado: 8, 197, 22, 4, 4, 11 y 67122)
SELECT 'departamentos' AS tabla, COUNT(*) AS filas FROM departamentos
UNION ALL SELECT 'municipios',      COUNT(*) FROM municipios
UNION ALL SELECT 'tipos_delito',    COUNT(*) FROM tipos_delito
UNION ALL SELECT 'generos',         COUNT(*) FROM generos
UNION ALL SELECT 'grupos_etarios',  COUNT(*) FROM grupos_etarios
UNION ALL SELECT 'medios',          COUNT(*) FROM medios
UNION ALL SELECT 'delitos_limpios', COUNT(*) FROM delitos_limpios;

-- V2. Registros y trazabilidad (esperado: 67122 y 67122)
SELECT COUNT(*) AS registros,
       COUNT(DISTINCT fila_origen) AS filas_origen_distintas,
       MIN(fila_origen) AS primera_fila_csv,
       MAX(fila_origen) AS ultima_fila_csv
FROM delitos_limpios;

-- V3. Registros sin catalogo asociado (esperado: 0)
SELECT COUNT(*) AS huerfanos
FROM delitos_limpios f
LEFT JOIN municipios m      ON m.id = f.municipio_id
LEFT JOIN tipos_delito t    ON t.id = f.tipo_delito_id
LEFT JOIN generos g         ON g.id = f.genero_id
LEFT JOIN grupos_etarios ge ON ge.id = f.grupo_etario_id
LEFT JOIN medios me         ON me.id = f.medio_id
WHERE m.id IS NULL OR t.id IS NULL OR g.id IS NULL OR ge.id IS NULL OR me.id IS NULL;

-- V4. Municipios cuyo prefijo no coincide con su departamento (esperado: 0)
SELECT COUNT(*) AS municipios_fuera_de_su_departamento
FROM municipios m
JOIN departamentos d ON d.id = m.departamento_id
WHERE LEFT(m.cod_dane, 2) <> d.cod_dane;

-- V5. Registros por departamento
-- (esperado: Atlantico 16664, Bolivar 13670, Magdalena 8725, Cesar 8613,
--  Cordoba 8372, Sucre 6413, La Guajira 3938, San Andres 727)
SELECT d.nombre AS departamento, COUNT(*) AS registros
FROM delitos_limpios f
JOIN municipios m    ON m.id = f.municipio_id
JOIN departamentos d ON d.id = m.departamento_id
GROUP BY d.nombre
ORDER BY registros DESC;

-- V6. Genero y grupo etario con su peso
-- (esperado: SIN DATO en genero 370, NO REPORTA 113, SIN DATO en grupo 68)
SELECT 'genero' AS variable, g.nombre AS categoria, COUNT(*) AS registros
FROM delitos_limpios f JOIN generos g ON g.id = f.genero_id
GROUP BY g.nombre
UNION ALL
SELECT 'grupo_etario', ge.nombre, COUNT(*)
FROM delitos_limpios f JOIN grupos_etarios ge ON ge.id = f.grupo_etario_id
GROUP BY ge.nombre
ORDER BY 1, 3 DESC;

-- V7. Atributos derivados
-- (esperado: repetidos 4688, en capitales 32131, menor de 14 38973)
SELECT
  (SELECT COUNT(*) FROM delitos_limpios WHERE es_repetido) AS repetidos,
  (SELECT COUNT(*) FROM delitos_limpios f JOIN municipios m ON m.id = f.municipio_id
    WHERE m.es_capital) AS en_capitales,
  (SELECT COUNT(*) FROM delitos_limpios f JOIN tipos_delito t ON t.id = f.tipo_delito_id
    WHERE t.es_menor_14) AS menor_14;

-- V8. Centros poblados y códigos DANE (esperado: 1415 registros
--     con sufijo distinto de 000, 477 códigos con sufijo distinto de 000
--     y 674 códigos completos distintos en todos los registros)
SELECT
    COUNT(*) FILTER (WHERE f.centro_poblado <> '000') AS registros_en_centro_poblado,
    COUNT(DISTINCT RTRIM(m.cod_dane::text) || RTRIM(f.centro_poblado::text))
        FILTER (WHERE f.centro_poblado <> '000') AS codigos_con_sufijo_no_000,
    COUNT(DISTINCT RTRIM(m.cod_dane::text) || RTRIM(f.centro_poblado::text))
        AS codigos_distintos
FROM delitos_limpios f
JOIN municipios m ON m.id = f.municipio_id;

-- V9. Fechas y cantidad (esperado: 2010-01-01, 2026-07-31 y suma 67122)
SELECT MIN(fecha_hecho) AS primera_fecha, MAX(fecha_hecho) AS ultima_fecha,
       SUM(cantidad) AS suma_cantidad
FROM delitos_limpios;

-- V10. Capitales (esperado: 8 municipios capitales)
--     La capitalidad se determina mediante es_capital, no por el sufijo DANE.
SELECT m.cod_dane, m.nombre AS municipio, d.nombre AS departamento, m.es_capital
FROM municipios m
JOIN departamentos d ON d.id = m.departamento_id
WHERE m.es_capital = TRUE
ORDER BY m.cod_dane;

-- V11. Prueba de lectura: los primeros registros con sus nombres
SELECT f.id, f.fila_origen, f.fecha_hecho, d.nombre AS departamento,
       m.nombre AS municipio, f.centro_poblado, t.articulo,
       g.nombre AS genero, ge.nombre AS grupo_etario, me.nombre AS medio,
       f.es_repetido
FROM delitos_limpios f
JOIN municipios m      ON m.id = f.municipio_id
JOIN departamentos d   ON d.id = m.departamento_id
JOIN tipos_delito t    ON t.id = f.tipo_delito_id
JOIN generos g         ON g.id = f.genero_id
JOIN grupos_etarios ge ON ge.id = f.grupo_etario_id
JOIN medios me         ON me.id = f.medio_id
ORDER BY f.id
LIMIT 10;

-- V12. Estructura para la documentacion (columnas, restricciones e indices)
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

SELECT conrelid::regclass AS tabla, conname AS restriccion,
       CASE contype WHEN 'p' THEN 'clave primaria' WHEN 'f' THEN 'clave foranea'
                    WHEN 'u' THEN 'unica' WHEN 'c' THEN 'check' END AS tipo
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
ORDER BY 1, 3;

SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;