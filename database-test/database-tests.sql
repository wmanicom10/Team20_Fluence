-- Test 1: Insert sample diseases
INSERT INTO diseases (name, category, severity_level, description) VALUES
('COVID-19', 'respiratory', 'high', 'Coronavirus disease caused by SARS-CoV-2'),
('Influenza', 'respiratory', 'moderate', 'Seasonal flu virus'),
('Malaria', 'vector-borne', 'high', 'Mosquito-borne parasitic disease'),
('Tuberculosis', 'respiratory', 'high', 'Bacterial infection affecting lungs'),
('Dengue Fever', 'vector-borne', 'moderate', 'Mosquito-borne viral infection');

-- Test 2: Insert sample locations
INSERT INTO locations (country, state_province, city, latitude, longitude, population, region_type) VALUES
('USA', 'New York', 'Syracuse', 43.0481, -76.1474, 142327, 'city'),
('USA', 'New York', 'New York City', 40.7128, -74.0060, 8336817, 'city'),
('USA', 'California', 'Los Angeles', 34.0522, -118.2437, 3979576, 'city'),
('USA', 'Texas', 'Houston', 29.7604, -95.3698, 2316797, 'city'),
('USA', 'Illinois', 'Chicago', 41.8781, -87.6298, 2693976, 'city'),
('USA', 'Florida', 'Miami', 25.7617, -80.1918, 439890, 'city');

-- Test 3: Insert sample API sources
INSERT INTO api_sources (name, api_endpoint, sync_frequency, is_active, auth_required) VALUES
('CDC Data API', 'https://data.cdc.gov/api', 60, TRUE, FALSE),
('WHO Global Health Observatory', 'https://ghoapi.azureedge.net/api', 120, TRUE, FALSE),
('Local Health Department', 'https://health.local.gov/api', 30, TRUE, TRUE);

-- Test 4: Insert sample verified cases
INSERT INTO cases (disease_id, location_id, case_count, date_reported, data_source, source_api, severity, verified) 
VALUES
(
  (SELECT disease_id FROM diseases WHERE name = 'COVID-19'),
  (SELECT location_id FROM locations WHERE city = 'Syracuse'),
  45, '2026-02-10', 'api', 'CDC Data API', 'moderate', TRUE
),
(
  (SELECT disease_id FROM diseases WHERE name = 'COVID-19'),
  (SELECT location_id FROM locations WHERE city = 'New York City'),
  523, '2026-02-10', 'api', 'CDC Data API', 'moderate', TRUE
),
(
  (SELECT disease_id FROM diseases WHERE name = 'COVID-19'),
  (SELECT location_id FROM locations WHERE city = 'Los Angeles'),
  892, '2026-02-10', 'api', 'CDC Data API', 'severe', TRUE
),
(
  (SELECT disease_id FROM diseases WHERE name = 'COVID-19'),
  (SELECT location_id FROM locations WHERE city = 'Houston'),
  367, '2026-02-10', 'api', 'CDC Data API', 'moderate', TRUE
),
(
  (SELECT disease_id FROM diseases WHERE name = 'Influenza'),
  (SELECT location_id FROM locations WHERE city = 'Syracuse'),
  12, '2026-02-12', 'api', 'CDC Data API', 'mild', TRUE
),
(
  (SELECT disease_id FROM diseases WHERE name = 'Influenza'),
  (SELECT location_id FROM locations WHERE city = 'New York City'),
  78, '2026-02-12', 'api', 'CDC Data API', 'mild', TRUE
),
(
  (SELECT disease_id FROM diseases WHERE name = 'Influenza'),
  (SELECT location_id FROM locations WHERE city = 'Chicago'),
  156, '2026-02-12', 'api', 'CDC Data API', 'moderate', TRUE
),
(
  (SELECT disease_id FROM diseases WHERE name = 'Malaria'),
  (SELECT location_id FROM locations WHERE city = 'Miami'),
  3, '2026-02-08', 'manual_submission', NULL, 'severe', TRUE
);

-- Query Test 1: Retrieve all diseases
SELECT 'TEST 1: Retrieve all diseases' AS test_description;
SELECT disease_id, name, category, severity_level 
FROM diseases 
ORDER BY name;

-- Query Test 2: Retrieve all locations
SELECT 'TEST 2: Retrieve all locations' AS test_description;
SELECT location_id, city, state_province, latitude, longitude, population 
FROM locations 
ORDER BY city;

-- Query Test 3: Retrieve all verified cases with disease and location details
SELECT 'TEST 3: Retrieve verified cases with joined data' AS test_description;
SELECT 
    c.case_id,
    d.name AS disease_name,
    l.city,
    l.state_province,
    c.case_count,
    c.date_reported,
    c.severity,
    c.data_source
FROM cases c
JOIN diseases d ON c.disease_id = d.disease_id
JOIN locations l ON c.location_id = l.location_id
WHERE c.verified = TRUE
ORDER BY c.date_reported DESC, c.case_count DESC;

-- Query Test 4: Get total cases by disease
SELECT 'TEST 4: Total cases by disease' AS test_description;
SELECT 
    d.name AS disease_name,
    COUNT(c.case_id) AS number_of_reports,
    SUM(c.case_count) AS total_cases
FROM diseases d
LEFT JOIN cases c ON d.disease_id = c.disease_id AND c.verified = TRUE
GROUP BY d.disease_id, d.name
ORDER BY total_cases DESC NULLS LAST;

-- Query Test 5: Get cases by location (for heat map)
SELECT 'TEST 5: Cases by location for heat map' AS test_description;
SELECT 
    l.city,
    l.state_province,
    l.latitude,
    l.longitude,
    d.name AS disease_name,
    SUM(c.case_count) AS total_cases
FROM locations l
JOIN cases c ON l.location_id = c.location_id
JOIN diseases d ON c.disease_id = d.disease_id
WHERE c.verified = TRUE
GROUP BY l.location_id, l.city, l.state_province, l.latitude, l.longitude, d.name
ORDER BY total_cases DESC;

-- Query Test 6: Filter cases by date range
SELECT 'TEST 6: Cases within date range' AS test_description;
SELECT 
    d.name AS disease_name,
    l.city,
    c.case_count,
    c.date_reported
FROM cases c
JOIN diseases d ON c.disease_id = d.disease_id
JOIN locations l ON c.location_id = l.location_id
WHERE c.date_reported >= '2026-02-01' 
  AND c.date_reported <= '2026-02-15'
  AND c.verified = TRUE
ORDER BY c.date_reported DESC;

-- Query Test 7: Get cases for a specific disease
SELECT 'TEST 7: Cases for COVID-19 only' AS test_description;
SELECT 
    l.city,
    l.state_province,
    c.case_count,
    c.date_reported,
    c.severity
FROM cases c
JOIN diseases d ON c.disease_id = d.disease_id
JOIN locations l ON c.location_id = l.location_id
WHERE d.name = 'COVID-19'
  AND c.verified = TRUE
ORDER BY c.case_count DESC;

-- Query Test 8: Verify row counts
SELECT 'TEST 8: Verify row counts' AS test_description;
SELECT 
    'diseases' AS table_name, COUNT(*) AS row_count FROM diseases
UNION ALL
SELECT 'locations', COUNT(*) FROM locations
UNION ALL
SELECT 'cases', COUNT(*) FROM cases
UNION ALL
SELECT 'api_sources', COUNT(*) FROM api_sources;

-- Validation Test 1: Check for duplicate diseases
SELECT 'VALIDATION 1: Check for duplicate diseases' AS test_description;
SELECT name, COUNT(*) as count
FROM diseases
GROUP BY name
HAVING COUNT(*) > 1;

-- Validation Test 2: Check for invalid case counts (should be >= 0)
SELECT 'VALIDATION 2: Check for invalid case counts' AS test_description;
SELECT case_id, case_count
FROM cases
WHERE case_count < 0;

-- Validation Test 3: Check for cases without location
SELECT 'VALIDATION 3: Check for orphaned cases' AS test_description;
SELECT c.case_id
FROM cases c
LEFT JOIN locations l ON c.location_id = l.location_id
WHERE l.location_id IS NULL;

-- Validation Test 4: Check for cases without disease
SELECT 'VALIDATION 4: Check for cases without disease' AS test_description;
SELECT c.case_id
FROM cases c
LEFT JOIN diseases d ON c.disease_id = d.disease_id
WHERE d.disease_id IS NULL;

SELECT 'DATABASE TESTS COMPLETED' AS status;
SELECT 
    (SELECT COUNT(*) FROM diseases) AS diseases_count,
    (SELECT COUNT(*) FROM locations) AS locations_count,
    (SELECT COUNT(*) FROM cases) AS cases_count,
    (SELECT COUNT(*) FROM api_sources) AS api_sources_count;