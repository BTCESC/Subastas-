CREATE TABLE IF NOT EXISTS usuarios (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    nombre_visible VARCHAR(120) NOT NULL,
    password_hash TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS autores (
    id BIGSERIAL PRIMARY KEY,
    nombre_principal VARCHAR(255) NOT NULL,
    notas TEXT,
    migracion_info TEXT,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_autores_nombre_principal_unico
ON autores (LOWER(TRIM(nombre_principal)));

CREATE TABLE IF NOT EXISTS autor_alias (
    id BIGSERIAL PRIMARY KEY,
    autor_id BIGINT NOT NULL REFERENCES autores(id) ON DELETE CASCADE,
    nombre_alias VARCHAR(255) NOT NULL,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_autor_alias_nombre_unico
ON autor_alias (LOWER(TRIM(nombre_alias)));

CREATE TABLE IF NOT EXISTS obras (
    id BIGSERIAL PRIMARY KEY,

    autor_id BIGINT NOT NULL REFERENCES autores(id) ON DELETE RESTRICT,
    creado_por BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,

    titulo VARCHAR(255) NOT NULL,
    tecnica VARCHAR(255),
    medidas VARCHAR(120),

    alto_cm NUMERIC(10, 2),
    ancho_cm NUMERIC(10, 2),
    superficie_cm2 NUMERIC(12, 2)
        GENERATED ALWAYS AS (
            CASE
                WHEN alto_cm IS NOT NULL AND ancho_cm IS NOT NULL
                THEN alto_cm * ancho_cm
                ELSE NULL
            END
        ) STORED,

    casa_subastas VARCHAR(255),
    fecha_subasta DATE,
    numero_lote VARCHAR(80),

    precio_salida NUMERIC(12, 2),
    comision_porcentaje NUMERIC(5, 2),
    precio_final NUMERIC(12, 2)
        GENERATED ALWAYS AS (
            CASE
                WHEN precio_salida IS NULL THEN NULL
                WHEN comision_porcentaje IS NULL THEN precio_salida
                ELSE ROUND(precio_salida * (1 + comision_porcentaje / 100), 2)
            END
        ) STORED,

    enlace_original TEXT,
    imagen_obra VARCHAR(255),
    imagen_ficha VARCHAR(255),
    notas TEXT,
    migracion_info TEXT,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_obras_alto_positivo CHECK (alto_cm IS NULL OR alto_cm > 0),
    CONSTRAINT chk_obras_ancho_positivo CHECK (ancho_cm IS NULL OR ancho_cm > 0),
    CONSTRAINT chk_obras_precio_salida_positivo CHECK (precio_salida IS NULL OR precio_salida >= 0),
    CONSTRAINT chk_obras_comision_positiva CHECK (comision_porcentaje IS NULL OR comision_porcentaje >= 0)
);

CREATE INDEX IF NOT EXISTS idx_obras_autor_id ON obras(autor_id);
CREATE INDEX IF NOT EXISTS idx_obras_titulo ON obras(LOWER(titulo));
CREATE INDEX IF NOT EXISTS idx_obras_casa_subastas ON obras(LOWER(casa_subastas));
CREATE INDEX IF NOT EXISTS idx_obras_fecha_subasta ON obras(fecha_subasta);
