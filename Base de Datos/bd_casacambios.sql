-- Crear tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    telefono VARCHAR(20) NOT NULL,
    direccion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_clientes_updated_at
BEFORE UPDATE ON clientes
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Crear tabla intermedia para la relación muchos a muchos
ALTER TABLE usuarios
ADD COLUMN cliente_activo_id BIGINT,
ADD CONSTRAINT fk_usuario_cliente_activo
    FOREIGN KEY (cliente_activo_id)
    REFERENCES clientes(id)
    ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS usuarios_clientes (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL,
    cliente_id BIGINT NOT NULL,
    CONSTRAINT fk_usuario_cliente_usuario 
        FOREIGN KEY (usuario_id) 
        REFERENCES usuarios(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_usuario_cliente_cliente 
        FOREIGN KEY (cliente_id) 
        REFERENCES clientes(id) 
        ON DELETE CASCADE,
    CONSTRAINT uk_usuario_cliente 
        UNIQUE (usuario_id, cliente_id)
);

-- Crear índices para optimizar las búsquedas
CREATE INDEX idx_cliente_nombre ON clientes(nombre);
CREATE INDEX idx_cliente_email ON clientes(email);