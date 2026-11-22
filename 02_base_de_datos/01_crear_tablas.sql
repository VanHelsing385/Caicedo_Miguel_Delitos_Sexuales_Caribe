-- =====================================================================
-- Delitos sexuales, region Caribe: esquema de la base de datos (Neon)
-- Contiene solo los datos ya limpios del Caribe (67.122 registros).
-- El script es idempotente: se puede ejecutar varias veces.
-- Nota: los comentarios de este archivo no usan punto y coma, porque
-- guardar_limpios.py separa las sentencias por ese caracter.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Catalogos (dimensiones)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departamentos (
    id        SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cod_dane  CHAR(2)     NOT NULL UNIQUE CHECK (cod_dane ~ '^[0-9]{2}$'),
    nombre    VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS municipios (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    departamento_id SMALLINT    NOT NULL REFERENCES departamentos (id),
    cod_dane        CHAR(5)     NOT NULL UNIQUE CHECK (cod_dane ~ '^[0-9]{5}$'),
    nombre          VARCHAR(60) NOT NULL,
    es_capital      BOOLEAN     NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_municipio_nombre UNIQUE (departamento_id, nombre)
);

CREATE TABLE IF NOT EXISTS tipos_delito (
    id          SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    articulo    VARCHAR(6)   NOT NULL,
    descripcion VARCHAR(150) NOT NULL UNIQUE,
    es_menor_14 BOOLEAN      NOT NULL
);

CREATE TABLE IF NOT EXISTS generos (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS grupos_etarios (
    id       SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre   VARCHAR(20) NOT NULL UNIQUE,
    edad_min SMALLINT,
    edad_max SMALLINT,
    CHECK (edad_min IS NULL OR edad_max IS NULL OR edad_min <= edad_max)
);

CREATE TABLE IF NOT EXISTS medios (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------
-- Tabla central (hechos): un registro por victima denunciada
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS delitos_limpios (
    id              INTEGER  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fila_origen     INTEGER  NOT NULL UNIQUE CHECK (fila_origen > 0),
    fecha_hecho     DATE     NOT NULL CHECK (fecha_hecho >= DATE '2010-01-01'),
    municipio_id    SMALLINT NOT NULL REFERENCES municipios (id),
    centro_poblado  CHAR(3)  NOT NULL CHECK (centro_poblado ~ '^[0-9]{3}$'),
    tipo_delito_id  SMALLINT NOT NULL REFERENCES tipos_delito (id),
    genero_id       SMALLINT NOT NULL REFERENCES generos (id),
    grupo_etario_id SMALLINT NOT NULL REFERENCES grupos_etarios (id),
    medio_id        SMALLINT NOT NULL REFERENCES medios (id),
    cantidad        SMALLINT NOT NULL CHECK (cantidad > 0),
    es_repetido     BOOLEAN  NOT NULL
);

-- ---------------------------------------------------------------------
-- Indices: columnas por las que se filtra y agrupa
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_dl_fecha     ON delitos_limpios (fecha_hecho);
CREATE INDEX IF NOT EXISTS idx_dl_municipio ON delitos_limpios (municipio_id);
CREATE INDEX IF NOT EXISTS idx_dl_tipo      ON delitos_limpios (tipo_delito_id);

-- ---------------------------------------------------------------------
-- Documentacion del esquema
-- ---------------------------------------------------------------------
COMMENT ON TABLE departamentos IS 'Departamentos de la región Caribe (código DANE de 2 dígitos)';
COMMENT ON TABLE municipios IS 'Municipios del Caribe presentes en los datos (código DANE de 5 dígitos)';
COMMENT ON TABLE tipos_delito IS 'Tipos de delito sexual tal como los nombra la fuente';
COMMENT ON TABLE generos IS 'Categorías de género de la fuente, incluidas SIN DATO y NO REPORTA';
COMMENT ON TABLE grupos_etarios IS 'Categorías etarias de la fuente policial, documentadas con referencia a la Ley 1098 de 2006';
COMMENT ON TABLE medios IS 'Medio o arma utilizado, tal como lo nombra la fuente';
COMMENT ON TABLE delitos_limpios IS 'Registros del Caribe ya limpios: ninguno eliminado, nulos como SIN DATO, repetidos marcados';

COMMENT ON COLUMN municipios.es_capital IS 'Atributo derivado: municipio con el sufijo (CT) en la fuente, capital del departamento';
COMMENT ON COLUMN tipos_delito.articulo IS 'Número de artículo del Código Penal extraído del texto, no es único (el 211 tiene varias descripciones)';
COMMENT ON COLUMN tipos_delito.es_menor_14 IS 'Atributo derivado: la descripción contiene MENOR DE 14';
COMMENT ON COLUMN grupos_etarios.edad_min IS 'Edad mínima definida para la categoría estadística de la fuente';
COMMENT ON COLUMN grupos_etarios.edad_max IS 'Edad máxima definida para la categoría estadística, nula cuando no aplica';
COMMENT ON COLUMN delitos_limpios.fila_origen IS 'Posición de la fila en el CSV original nacional, para rastrear cada registro';
COMMENT ON COLUMN delitos_limpios.centro_poblado IS 'Tres últimos dígitos del código DANE original, conservados para reconstruir el código completo';
COMMENT ON COLUMN delitos_limpios.es_repetido IS 'Fila idéntica a otra anterior en todas las columnas originales: se marca, no se elimina';