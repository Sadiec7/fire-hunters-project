-- ============================================================================
-- ia/db_schema_sflame.sql
-- Esquema Oficial PostgreSQL de 6 Tablas para NASA Space Apps: Flame in Freefall
-- Autores: Ángel ("Lito" / "Perrita") & Cristofer
-- ============================================================================

BEGIN;

-- 1. TABLA DE INVESTIGACIONES (Separa s-Flame activo en el solver 3D de otras campañas)
CREATE TABLE IF NOT EXISTS investigations (
    investigation_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    facility VARCHAR(100) NOT NULL,
    configuration_type VARCHAR(80) NOT NULL,
    is_active_for_3d_solver BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT
);

-- 2. TABLA DE EXPERIMENTOS
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id VARCHAR(50) PRIMARY KEY,
    investigation_id VARCHAR(50) NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    nasa_run_code VARCHAR(30),
    fuel_type VARCHAR(20) NOT NULL,
    burner_radius_m DOUBLE PRECISION NOT NULL,
    residual_gravity_m_s2 DOUBLE PRECISION NOT NULL DEFAULT 1.0e-4,
    notes TEXT
);

-- 3. TABLA DE CONDICIONES DE OPERACIÓN EN UNIDADES SI
CREATE TABLE IF NOT EXISTS conditions (
    condition_id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL UNIQUE REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    fuel_type VARCHAR(20) NOT NULL,
    Y_F_burner DOUBLE PRECISION NOT NULL CHECK (Y_F_burner >= 0.0 AND Y_F_burner <= 1.0),
    diluent_species VARCHAR(20) NOT NULL DEFAULT 'N2',
    Y_O_ambient DOUBLE PRECISION NOT NULL CHECK (Y_O_ambient >= 0.0 AND Y_O_ambient <= 1.0),
    pressure_Pa DOUBLE PRECISION NOT NULL CHECK (pressure_Pa > 0.0),
    T_initial_K DOUBLE PRECISION NOT NULL CHECK (T_initial_K > 0.0),
    T_burner_K DOUBLE PRECISION NOT NULL CHECK (T_burner_K > 0.0),
    mass_flow_kg_s DOUBLE PRECISION NOT NULL CHECK (mass_flow_kg_s >= 0.0),
    burner_radius_m DOUBLE PRECISION NOT NULL CHECK (burner_radius_m > 0.0),
    provenance_tag VARCHAR(50) NOT NULL
);

-- 4. TABLA DE MEDICIONES EXPERIMENTALES (Incluye perfiles radiales JSONB para MAE/RMSE)
CREATE TABLE IF NOT EXISTS measurements (
    measurement_id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL UNIQUE REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    measured_flame_radius_m DOUBLE PRECISION NOT NULL,
    measured_max_temp_K DOUBLE PRECISION NOT NULL,
    radial_r_m_array JSONB,
    radial_T_K_array JSONB,
    extinction_observed BOOLEAN NOT NULL DEFAULT FALSE,
    units_si VARCHAR(50) NOT NULL DEFAULT 'm, K'
);

-- 5. TABLA DE ARCHIVOS Y TRAZABILIDAD BIBLIOGRÁFICA NASA PSI
CREATE TABLE IF NOT EXISTS files (
    file_id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    file_name VARCHAR(150) NOT NULL,
    psi_source_document TEXT NOT NULL,
    access_status VARCHAR(30) NOT NULL CHECK (access_status IN ('PUBLIC_VERIFIED', 'PUBLIC_OPEN', 'RESTRICTED'))
);

-- 6. TABLA DE INCERTIDUMBRES Y PROCEDENCIA
CREATE TABLE IF NOT EXISTS uncertainties (
    uncertainty_id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    variable_name VARCHAR(60) NOT NULL,
    abs_uncertainty_si DOUBLE PRECISION NOT NULL,
    rel_uncertainty_pct DOUBLE PRECISION NOT NULL,
    confidence_level DOUBLE PRECISION NOT NULL DEFAULT 0.95,
    provenance_classification VARCHAR(50) NOT NULL
);

-- ============================================================================
-- CARGA DE CAMPAÑAS (Regla Estricta Sección 2.2: Solo ACME_S_FLAME activa en 3D)
-- ============================================================================
INSERT INTO investigations (investigation_id, title, facility, configuration_type, is_active_for_3d_solver, description)
VALUES
    ('ACME_S_FLAME', 'ACME Spherical Flame (s-Flame)', 'ISS_CIR', 'SPHERICAL_POROUS_BURNER', TRUE,
     'Investigación oficial de llamas esféricas de difusión en microgravedad en el Combustion Integrated Rack (CIR). Única campaña válida para calibrar y validar el solver diferencial 3D.'),
    ('SYN-BASS', 'Synthetic BASS-II Solid Fuel Scenarios', 'ISS_MSG_SPICE', 'SOLID_SLAB_TUNNEL', FALSE,
     'Escenarios sintéticos de quema de sólidos en túnel de viento (PSI-25). Exclusivo para contexto en Red Bayesiana; prohibido en el solver 3D.'),
    ('SYN-FLEX', 'Synthetic FLEX Droplet Combustion Scenarios', 'ISS_CIR', 'LIQUID_DROPLET', FALSE,
     'Escenarios sintéticos de combustión de gotas líquidas (PSI-69). Exclusivo para contexto en Red Bayesiana; prohibido en el solver 3D.'),
    ('SYN-SAFFIRE', 'Synthetic SAFFIRE Large Scale Enclosure Fire', 'CYGNUS_SPACECRAFT', 'LARGE_SOLID_PANEL', FALSE,
     'Escenarios sintéticos de fuego a gran escala en vehículo Cygnus (PSI-98). Exclusivo para contexto en Red Bayesiana; prohibido en el solver 3D.')
ON CONFLICT (investigation_id) DO NOTHING;

-- ============================================================================
-- CARGA DE CORRIDAS REALES DE NASA s-Flame (Desde nasa_sflame_experiments.csv)
-- ============================================================================
INSERT INTO experiments (experiment_id, investigation_id, nasa_run_code, fuel_type, burner_radius_m, residual_gravity_m_s2, notes)
VALUES
    ('SFLAME_REF_C2H4', 'ACME_S_FLAME', 'REF_C2H4', 'C2H4', 0.00318, 1.0e-4, 'Caso maestro de referencia para verificación 1D/3D (2.5 mg/s C2H4 puro en aire a 98 kPa).'),
    ('SFLAME_39B3',     'ACME_S_FLAME', '39B3',     'C2H4', 0.00318, 1.0e-4, 'Corrida ISS s-Flame de etileno puro a 1 atm en aire estándar.'),
    ('SFLAME_51A1',     'ACME_S_FLAME', '51A1',     'C2H4', 0.00318, 1.0e-4, 'Corrida ISS s-Flame de etileno diluido con N2 (Y_F=0.50) a 1 atm.'),
    ('SFLAME_87D1',     'ACME_S_FLAME', '87D1',     'CH4',  0.00318, 1.0e-4, 'Corrida ISS s-Flame de metano puro a 1 atm en aire.'),
    ('SFLAME_94A4',     'ACME_S_FLAME', '94A4',     'CH4',  0.00318, 1.0e-4, 'Corrida ISS s-Flame de metano diluido en atmósfera enriquecida de O2.'),
    ('SFLAME_H2_01',    'ACME_S_FLAME', 'H2_01',    'H2',   0.00318, 1.0e-4, 'Corrida s-Flame de hidrógeno diluido en nitrógeno (Y_F=0.15) a 1 atm.'),
    ('SFLAME_H2_02',    'ACME_S_FLAME', 'H2_02',    'H2',   0.00318, 1.0e-4, 'Corrida s-Flame de hidrógeno diluido (Y_F=0.25) a presión reducida de 85 kPa.')
ON CONFLICT (experiment_id) DO NOTHING;

-- Condiciones de operación en SI
INSERT INTO conditions (experiment_id, fuel_type, Y_F_burner, diluent_species, Y_O_ambient, pressure_Pa, T_initial_K, T_burner_K, mass_flow_kg_s, burner_radius_m, provenance_tag)
VALUES
    ('SFLAME_REF_C2H4', 'C2H4', 1.000, 'NONE', 0.233,  98000.0, 298.15, 300.0, 2.50e-6, 0.00318, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_39B3',     'C2H4', 1.000, 'NONE', 0.233, 101325.0, 298.15, 300.0, 2.50e-6, 0.00318, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_51A1',     'C2H4', 0.500, 'N2',   0.233, 101325.0, 298.15, 300.0, 3.20e-6, 0.00318, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_87D1',     'CH4',  1.000, 'NONE', 0.233, 101325.0, 298.15, 300.0, 2.20e-6, 0.00318, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_94A4',     'CH4',  0.600, 'N2',   0.260, 101325.0, 298.15, 300.0, 2.80e-6, 0.00318, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_H2_01',    'H2',   0.150, 'N2',   0.233, 101325.0, 298.15, 300.0, 1.80e-6, 0.00318, 'ESTIMADO_FUENTE_CIENTIFICA'),
    ('SFLAME_H2_02',    'H2',   0.250, 'N2',   0.210,  85000.0, 298.15, 300.0, 2.10e-6, 0.00318, 'ESTIMADO_FUENTE_CIENTIFICA')
ON CONFLICT (experiment_id) DO NOTHING;

-- Mediciones experimentales y perfil radial para el caso maestro
INSERT INTO measurements (experiment_id, measured_flame_radius_m, measured_max_temp_K, radial_r_m_array, radial_T_K_array, extinction_observed)
VALUES
    ('SFLAME_REF_C2H4', 0.0224, 1677.0,
     '[0.00318, 0.006, 0.010, 0.015, 0.019, 0.0224, 0.026, 0.030, 0.035]'::jsonb,
     '[300.0, 620.0, 1040.0, 1390.0, 1585.0, 1677.0, 1410.0, 980.0, 480.0]'::jsonb, FALSE),
    ('SFLAME_39B3',     0.0221, 1685.0, NULL, NULL, FALSE),
    ('SFLAME_51A1',     0.0175, 1540.0, NULL, NULL, FALSE),
    ('SFLAME_87D1',     0.0210, 1620.0, NULL, NULL, FALSE),
    ('SFLAME_94A4',     0.0182, 1690.0, NULL, NULL, FALSE),
    ('SFLAME_H2_01',    0.0195, 1750.0, NULL, NULL, FALSE),
    ('SFLAME_H2_02',    0.0235, 1810.0, NULL, NULL, FALSE)
ON CONFLICT (experiment_id) DO NOTHING;

-- Archivos fuente y documentos de referencia
INSERT INTO files (experiment_id, file_name, psi_source_document, access_status)
VALUES
    ('SFLAME_REF_C2H4', 'sflame_reference_case.json', 'Sunderland et al. (2005) / Santa et al. (2007) Spherical Diffusion Flames', 'PUBLIC_VERIFIED'),
    ('SFLAME_39B3',     'nasa_sflame_experiments.csv', 'NASA PSI ACME s-Flame Test Matrix ISS CIR', 'PUBLIC_VERIFIED'),
    ('SFLAME_51A1',     'nasa_sflame_experiments.csv', 'NASA PSI ACME s-Flame Test Matrix ISS CIR', 'PUBLIC_VERIFIED'),
    ('SFLAME_87D1',     'nasa_sflame_experiments.csv', 'NASA PSI ACME s-Flame Test Matrix ISS CIR', 'PUBLIC_VERIFIED'),
    ('SFLAME_94A4',     'nasa_sflame_experiments.csv', 'NASA PSI ACME s-Flame Test Matrix ISS CIR', 'PUBLIC_VERIFIED'),
    ('SFLAME_H2_01',    'nasa_sflame_experiments.csv', 'Tse et al. / Tang et al. Microgravity Spherical H2 Flames', 'PUBLIC_VERIFIED'),
    ('SFLAME_H2_02',    'nasa_sflame_experiments.csv', 'Tse et al. / Tang et al. Microgravity Spherical H2 Flames', 'PUBLIC_VERIFIED');

-- Incertidumbres experimentales documentadas
INSERT INTO uncertainties (experiment_id, variable_name, abs_uncertainty_si, rel_uncertainty_pct, confidence_level, provenance_classification)
VALUES
    ('SFLAME_REF_C2H4', 'measured_flame_radius_m', 0.0005, 2.23, 0.95, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_REF_C2H4', 'measured_max_temp_K',     50.0,   2.98, 0.95, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_39B3',     'measured_flame_radius_m', 0.0005, 2.26, 0.95, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_39B3',     'measured_max_temp_K',     50.0,   2.97, 0.95, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_51A1',     'measured_flame_radius_m', 0.0005, 2.86, 0.95, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_87D1',     'measured_flame_radius_m', 0.0006, 2.86, 0.95, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_94A4',     'measured_flame_radius_m', 0.0005, 2.75, 0.95, 'MEDIDO_EXPERIMENTALMENTE'),
    ('SFLAME_H2_01',    'measured_flame_radius_m', 0.0006, 3.08, 0.95, 'ESTIMADO_FUENTE_CIENTIFICA'),
    ('SFLAME_H2_02',    'measured_flame_radius_m', 0.0006, 2.55, 0.95, 'ESTIMADO_FUENTE_CIENTIFICA');

COMMIT;