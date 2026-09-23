-- KAIJU Crisis Manager - PostgreSQL database schema
-- Designed for PostgreSQL / Neon

CREATE TYPE user_role AS ENUM (
    'QC',
    'LC',
    'CD'
);

CREATE TYPE request_status AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED',
    'CANCELLED',
    'COMPLETED'
);

CREATE TYPE transfer_status AS ENUM (
    'PENDING',
    'IN_TRANSIT',
    'DELIVERED',
    'CANCELLED'
);

CREATE TYPE reservation_status AS ENUM (
    'PENDING',
    'APPROVED',
    'CANCELLED',
    'COMPLETED'
);

CREATE TYPE route_type AS ENUM (
    'LAND',
    'MARITIME',
    'TRANSIT'
);

CREATE TABLE quarters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    disaster_level SMALLINT NOT NULL DEFAULT 1
        CHECK (disaster_level BETWEEN 1 AND 5),
    sea_access BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role user_role,
    quarter_id INTEGER REFERENCES quarters(id) ON DELETE SET NULL
);

-- LC's multi-quarter scope: one row per (user, quarter) they're assigned to.
CREATE TABLE user_quarters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quarter_id INTEGER NOT NULL REFERENCES quarters(id) ON DELETE CASCADE,
    UNIQUE (user_id, quarter_id)
);

CREATE TABLE resource_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
);

CREATE TABLE quarter_resources (
    id SERIAL PRIMARY KEY,
    quarter_id INTEGER NOT NULL REFERENCES quarters(id) ON DELETE CASCADE,
    resource_type_id INTEGER NOT NULL REFERENCES resource_types(id) ON DELETE CASCADE,
    initial_quantity INTEGER NOT NULL CHECK (initial_quantity >= 0),
    available_quantity INTEGER NOT NULL CHECK (available_quantity >= 0),
    reserved_quantity INTEGER NOT NULL DEFAULT 0 CHECK (reserved_quantity >= 0),
    UNIQUE (quarter_id, resource_type_id),
    CHECK (available_quantity + reserved_quantity <= initial_quantity)
);

CREATE TABLE quarter_connections (
    id SERIAL PRIMARY KEY,
    from_quarter_id INTEGER NOT NULL REFERENCES quarters(id) ON DELETE CASCADE,
    to_quarter_id INTEGER NOT NULL REFERENCES quarters(id) ON DELETE CASCADE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (from_quarter_id, to_quarter_id),
    CHECK (from_quarter_id <> to_quarter_id)
);

CREATE TABLE requests (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    source_quarter_id INTEGER NOT NULL REFERENCES quarters(id) ON DELETE RESTRICT,
    destination_quarter_id INTEGER NOT NULL REFERENCES quarters(id) ON DELETE RESTRICT,
    resource_type_id INTEGER NOT NULL REFERENCES resource_types(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    status request_status NOT NULL DEFAULT 'PENDING',
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (source_quarter_id <> destination_quarter_id)
);

CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    quarter_id INTEGER NOT NULL REFERENCES quarters(id) ON DELETE RESTRICT,
    resource_type_id INTEGER NOT NULL REFERENCES resource_types(id) ON DELETE RESTRICT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    status reservation_status NOT NULL DEFAULT 'PENDING',
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_at > start_at)
);

CREATE TABLE transfers (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL UNIQUE REFERENCES requests(id) ON DELETE RESTRICT,
    source_quarter_id INTEGER NOT NULL REFERENCES quarters(id) ON DELETE RESTRICT,
    destination_quarter_id INTEGER NOT NULL REFERENCES quarters(id) ON DELETE RESTRICT,
    resource_type_id INTEGER NOT NULL REFERENCES resource_types(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    route_type route_type NOT NULL,
    status transfer_status NOT NULL DEFAULT 'PENDING',
    departure_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    CHECK (source_quarter_id <> destination_quarter_id),
    CHECK (
        delivered_at IS NULL
        OR departure_at IS NULL
        OR delivered_at >= departure_at
    )
);

-- Initial quarters
INSERT INTO quarters (name, disaster_level, sea_access) VALUES
    ('Apex', 1, FALSE),
    ('Echo', 1, TRUE),
    ('Warden', 1, FALSE),
    ('Xeno', 1, TRUE),
    ('Zion', 1, TRUE);

-- Resource types from the KAIJU specification
INSERT INTO resource_types (name) VALUES
    ('Medical personnel'),
    ('Rescue teams'),
    ('Transport vehicles'),
    ('Emergency shelters'),
    ('Food & water supplies'),
    ('Communication equipment'),
    ('Power generators'),
    ('Engineering crews'),
    ('Security units'),
    ('Hazmat equipment');

-- Land adjacency.
-- Connections are stored in both directions for simple lookup.
INSERT INTO quarter_connections (from_quarter_id, to_quarter_id)
SELECT q1.id, q2.id
FROM quarters q1
JOIN quarters q2 ON (q1.name, q2.name) IN (
    ('Apex', 'Echo'), ('Echo', 'Apex'),
    ('Apex', 'Warden'), ('Warden', 'Apex'),
    ('Apex', 'Xeno'), ('Xeno', 'Apex'),
    ('Echo', 'Xeno'), ('Xeno', 'Echo'),
    ('Warden', 'Xeno'), ('Xeno', 'Warden'),
    ('Warden', 'Zion'), ('Zion', 'Warden'),
    ('Xeno', 'Zion'), ('Zion', 'Xeno')
);

CREATE INDEX idx_users_quarter
    ON users(quarter_id);

CREATE INDEX idx_quarter_resources_quarter
    ON quarter_resources(quarter_id);

CREATE INDEX idx_requests_status
    ON requests(status);

CREATE INDEX idx_requests_destination
    ON requests(destination_quarter_id);

CREATE INDEX idx_transfers_status
    ON transfers(status);

CREATE INDEX idx_reservations_quarter
    ON reservations(quarter_id);

CREATE INDEX idx_reservations_user
    ON reservations(user_id);

CREATE INDEX idx_reservations_dates
    ON reservations(start_at, end_at);

CREATE INDEX idx_connections_from
    ON quarter_connections(from_quarter_id);

CREATE INDEX idx_connections_to
    ON quarter_connections(to_quarter_id);
