-- ============================================================================
-- ARCHIVO: ia/db_schema_sflame.sql
-- RESPONSABLE: Ángel ("Lito" / "Perrita")
-- DESCRIPCIÓN: Esquema relacional de 6 tablas para PostgreSQL / Supabase
--              con trazabilidad directa a NASA PSI-23 (286 archivos de
--              mediciones y 288 archivos MFC en 18 jornadas experimentales).
-- ============================================================================

DROP TABLE IF EXISTS uncertainties CASCADE;
DROP TABLE IF EXISTS files CASCADE;
DROP TABLE IF EXISTS measurements CASCADE;
DROP TABLE IF EXISTS conditions CASCADE;
DROP TABLE IF EXISTS experiments CASCADE;
DROP TABLE IF EXISTS investigations CASCADE;

-- 1. Tabla de Investigaciones (Campañas de microgravedad)
CREATE TABLE investigations (
    investigation_id VARCHAR(50) PRIMARY KEY,
    psi_dataset_id VARCHAR(30) NOT NULL DEFAULT 'PSI-23',
    title VARCHAR(200) NOT NULL,
    facility VARCHAR(100) NOT NULL,
    is_active_for_3d_solver BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT
);

-- 2. Tabla de Experimentos (Con las 3 columnas nuevas para IGNIS-mu / PSI-23)
CREATE TABLE experiments (
    experiment_id VARCHAR(50) PRIMARY KEY,
    investigation_id VARCHAR(50) NOT NULL REFERENCES investigations(investigation_id),
    psi_id VARCHAR(30) NOT NULL DEFAULT 'PSI-23',
    mfc_config_file VARCHAR(100) NOT NULL,
    test_day_id VARCHAR(40) NOT NULL,
    fuel_type VARCHAR(20) NOT NULL,
    diluent_species VARCHAR(20) NOT NULL DEFAULT 'N2',
    is_reference_case BOOLEAN NOT NULL DEFAULT FALSE,
    provenance_tag VARCHAR(50) NOT NULL DEFAULT 'MEDIDO_EXPERIMENTALMENTE'
);

-- 3. Tabla de Condiciones de Operación en Unidades SI
CREATE TABLE conditions (
    condition_id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    Y_F_burner DOUBLE PRECISION NOT NULL CHECK (Y_F_burner > 0.0 AND Y_F_burner <= 1.0),
    Y_I_burner DOUBLE PRECISION NOT NULL CHECK (Y_I_burner >= 0.0 AND Y_I_burner < 1.0),
    Y_O_ambient DOUBLE PRECISION NOT NULL CHECK (Y_O_ambient > 0.0 AND Y_O_ambient <= 1.0),
    pressure_Pa DOUBLE PRECISION NOT NULL CHECK (pressure_Pa > 0.0),
    T_ambient_K DOUBLE PRECISION NOT NULL CHECK (T_ambient_K > 0.0),
    T_burner_K DOUBLE PRECISION NOT NULL CHECK (T_burner_K > 0.0),
    mass_flow_kg_s DOUBLE PRECISION NOT NULL CHECK (mass_flow_kg_s > 0.0),
    burner_radius_m DOUBLE PRECISION NOT NULL CHECK (burner_radius_m > 0.0)
);

-- 4. Tabla de Mediciones Experimentales en Unidades SI
CREATE TABLE measurements (
    measurement_id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    measured_flame_radius_m DOUBLE PRECISION NOT NULL,
    measured_max_temp_K DOUBLE PRECISION NOT NULL,
    radiative_power_W DOUBLE PRECISION,
    steady_state_achieved BOOLEAN NOT NULL DEFAULT TRUE
);

-- 5. Tabla de Archivos Asociados (286 mediciones + 288 MFC configs en PSI-23)
CREATE TABLE files (
    file_id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    file_name VARCHAR(150) NOT NULL,
    file_Category VARCHAR(50) NOT NULL, -- 'MFC_CONFIG', 'THERMOCOUPLE_RAW', 'RADIOMETER', 'IMAGE_3D'
    storage_uri TEXT NOT NULL
);

-- 6. Tabla de Incertidumbres Experimentales Documentadas
CREATE TABLE uncertainties (
    uncertainty_id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    uncertainty_radius_m DOUBLE PRECISION NOT NULL,
    uncertainty_temp_K DOUBLE PRECISION NOT NULL,
    mfc_flow_uncertainty_rel DOUBLE PRECISION NOT NULL DEFAULT 0.02
);

-- ============================================================================
-- INSERCIÓN DE CAMPAÑAS (Regla de Oro 1: Exclusividad s-Flame en Solver 3D)
-- ============================================================================
INSERT INTO investigations (investigation_id, psi_dataset_id, title, facility, is_active_for_3d_solver, description) VALUES
('ACME_S_FLAME', 'PSI-23', 'Advanced Combustion via Microgravity Experiments - Spherical Flame', 'ISS CIR (Combustion Integrated Rack)', TRUE, 'Quemador poroso esférico gaseoso (r_b = 0.00318 m). Única campaña activa para el solver 3D.'),
('SYN-BASS', 'PSI-SYN', 'Burning and Suppression of Solids II (Sintético)', 'ISS MSG', FALSE, 'Combustión de sólidos en túnel. Inactivo para el solver esférico 3D.'),
('SYN-FLEX', 'PSI-SYN', 'Flame Extinguishment Experiment (Sintético)', 'ISS CIR', FALSE, 'Combustión de gotas líquidas. Inactivo para el solver gaseoso s-Flame.'),
('SYN-SAFFIRE', 'PSI-SYN', 'Spacecraft Fire Experiment (Sintético)', 'Cygnus Vehicle', FALSE, 'Propagación en paneles sólidos a gran escala. Inactivo para el solver 3D.');

-- ============================================================================
-- INSERCIÓN DE CORRIDAS DE S-FLAME VINCULADAS A PSI-23
-- ============================================================================
INSERT INTO experiments (experiment_id, investigation_id, psi_id, mfc_config_file, test_day_id, fuel_type, diluent_species, is_reference_case, provenance_tag) VALUES
('SFLAME_REF_C2H4', 'ACME_S_FLAME', 'PSI-23', 'MFC_CFG_REF_C2H4.csv', 'CIR_DAY_01', 'C2H4', 'N2', TRUE,  'MEDIDO_EXPERIMENTALMENTE'),
('SFLAME_39B3',     'ACME_S_FLAME', 'PSI-23', 'MFC_CFG_39B3.csv',     'CIR_DAY_04', 'C2H4', 'N2', FALSE, 'MEDIDO_EXPERIMENTALMENTE'),
('SFLAME_51A1',     'ACME_S_FLAME', 'PSI-23', 'MFC_CFG_51A1.csv',     'CIR_DAY_07', 'C2H4', 'N2', FALSE, 'MEDIDO_EXPERIMENTALMENTE'),
('SFLAME_87D1',     'ACME_S_FLAME', 'PSI-23', 'MFC_CFG_87D1.csv',     'CIR_DAY_11', 'CH4',  'N2', FALSE, 'MEDIDO_EXPERIMENTALMENTE'),
('SFLAME_94A4',     'ACME_S_FLAME', 'PSI-23', 'MFC_CFG_94A4.csv',     'CIR_DAY_14', 'CH4',  'N2', FALSE, 'MEDIDO_EXPERIMENTALMENTE'),
('SFLAME_H2_01',    'ACME_S_FLAME', 'PSI-23', 'MFC_CFG_H2_01.csv',    'CIR_DAY_16', 'H2',   'N2', FALSE, 'MEDIDO_EXPERIMENTALMENTE'),
('SFLAME_H2_02',    'ACME_S_FLAME', 'PSI-23', 'MFC_CFG_H2_02.csv',    'CIR_DAY_18', 'H2',   'He', FALSE, 'MEDIDO_EXPERIMENTALMENTE');

INSERT INTO conditions (experiment_id, Y_F_burner, Y_I_burner, Y_O_ambient, pressure_Pa, T_ambient_K, T_burner_K, mass_flow_kg_s, burner_radius_m) VALUES
('SFLAME_REF_C2H4', 1.000, 0.000, 0.233, 98000.0,  298.15, 300.0, 2.50e-6, 0.00318),
('SFLAME_39B3',     1.000, 0.000, 0.233, 101325.0, 298.15, 300.0, 2.50e-6, 0.00318),
('SFLAME_51A1',     0.500, 0.500, 0.233, 101325.0, 298.15, 300.0, 3.20e-6, 0.00318),
('SFLAME_87D1',     1.000, 0.000, 0.233, 101325.0, 298.15, 300.0, 2.20e-6, 0.00318),
('SFLAME_94A4',     0.600, 0.400, 0.260, 101325.0, 298.15, 300.0, 2.80e-6, 0.00318),
('SFLAME_H2_01',    0.150, 0.850, 0.233, 101325.0, 298.15, 300.0, 1.80e-6, 0.00318),
('SFLAME_H2_02',    0.250, 0.750, 0.210, 85000.0,  298.15, 300.0, 2.10e-6, 0.00318);

INSERT INTO measurements (experiment_id, measured_flame_radius_m, measured_max_temp_K, radiative_power_W, steady_state_achieved) VALUES
('SFLAME_REF_C2H4', 0.0224, 1677.0, 38.5, TRUE),
('SFLAME_39B3',     0.0221, 1685.0, 39.2, TRUE),
('SFLAME_51A1',     0.0175, 1540.0, 22.8, TRUE),
('SFLAME_87D1',     0.0210, 1620.0, 34.1, TRUE),
('SFLAME_94A4',     0.0182, 1690.0, 27.6, TRUE),
('SFLAME_H2_01',    0.0195, 1750.0, 18.4, TRUE),
('SFLAME_H2_02',    0.0235, 1810.0, 29.0, TRUE);

INSERT INTO uncertainties (experiment_id, uncertainty_radius_m, uncertainty_temp_K, mfc_flow_uncertainty_rel) VALUES
('SFLAME_REF_C2H4', 0.0005, 50.0, 0.02),
('SFLAME_39B3',     0.0005, 50.0, 0.02),
('SFLAME_51A1',     0.0005, 45.0, 0.02),
('SFLAME_87D1',     0.0006, 50.0, 0.02),
('SFLAME_94A4',     0.0005, 50.0, 0.02),
('SFLAME_H2_01',    0.0006, 55.0, 0.02),
('SFLAME_H2_02',    0.0006, 55.0, 0.02);