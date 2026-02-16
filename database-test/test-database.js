import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = 'https://rogzdnrmmsdlpxjbgtvj.supabase.co';
const supabaseKey = 'sb_publishable_yinNcPmYmUIaIGSpkNJCjQ_vPxrnSbZ';
const supabase = createClient(supabaseUrl, supabaseKey);

// Test results tracker
let testsRun = 0;
let testsPassed = 0;
let testsFailed = 0;

/**
 * Helper function to log test results
 */
function logTest(testName, passed, message = '') {
  testsRun++;
  if (passed) {
    testsPassed++;
    console.log(`✅ PASS: ${testName}`);
    if (message) console.log(`   ${message}`);
  } else {
    testsFailed++;
    console.log(`❌ FAIL: ${testName}`);
    if (message) console.log(`   ${message}`);
  }
  console.log('');
}

/**
 * Test 1: Insert a disease
 */
async function testInsertDisease() {
  console.log('--- Test 1: Insert Disease ---');
  
  try {
    const { data, error } = await supabase
      .from('diseases')
      .insert({
        name: 'Measles',
        category: 'viral',
        severity_level: 'moderate',
        description: 'Highly contagious viral infection'
      })
      .select();

    if (error) throw error;
    
    logTest(
      'Insert Disease', 
      data && data.length > 0,
      `Inserted disease: ${data[0].name} (ID: ${data[0].disease_id})`
    );
    
    return data[0];
  } catch (error) {
    logTest('Insert Disease', false, error.message);
    return null;
  }
}

/**
 * Test 2: Insert a location
 */
async function testInsertLocation() {
  console.log('--- Test 2: Insert Location ---');
  
  try {
    const { data, error } = await supabase
      .from('locations')
      .insert({
        country: 'USA',
        state_province: 'Massachusetts',
        city: 'Boston',
        latitude: 42.3601,
        longitude: -71.0589,
        population: 675647,
        region_type: 'city'
      })
      .select();

    if (error) throw error;
    
    logTest(
      'Insert Location',
      data && data.length > 0,
      `Inserted location: ${data[0].city}, ${data[0].state_province} (ID: ${data[0].location_id})`
    );
    
    return data[0];
  } catch (error) {
    logTest('Insert Location', false, error.message);
    return null;
  }
}

/**
 * Test 3: Insert a case
 */
async function testInsertCase(diseaseId, locationId) {
  console.log('--- Test 3: Insert Case ---');
  
  if (!diseaseId || !locationId) {
    logTest('Insert Case', false, 'Missing disease_id or location_id');
    return null;
  }
  
  try {
    const { data, error } = await supabase
      .from('cases')
      .insert({
        disease_id: diseaseId,
        location_id: locationId,
        case_count: 25,
        date_reported: '2026-02-15',
        data_source: 'manual_submission',
        severity: 'moderate',
        verified: true
      })
      .select();

    if (error) throw error;
    
    logTest(
      'Insert Case',
      data && data.length > 0,
      `Inserted case: ${data[0].case_count} cases (ID: ${data[0].case_id})`
    );
    
    return data[0];
  } catch (error) {
    logTest('Insert Case', false, error.message);
    return null;
  }
}

/**
 * Test 4: Query all diseases
 */
async function testQueryDiseases() {
  console.log('--- Test 4: Query All Diseases ---');
  
  try {
    const { data, error } = await supabase
      .from('diseases')
      .select('*')
      .order('name');

    if (error) throw error;
    
    logTest(
      'Query All Diseases',
      data && data.length > 0,
      `Found ${data.length} disease(s): ${data.map(d => d.name).join(', ')}`
    );
    
    return data;
  } catch (error) {
    logTest('Query All Diseases', false, error.message);
    return null;
  }
}

/**
 * Test 5: Query all locations
 */
async function testQueryLocations() {
  console.log('--- Test 5: Query All Locations ---');
  
  try {
    const { data, error } = await supabase
      .from('locations')
      .select('*')
      .order('city');

    if (error) throw error;
    
    logTest(
      'Query All Locations',
      data && data.length > 0,
      `Found ${data.length} location(s): ${data.map(l => `${l.city}, ${l.state_province}`).join('; ')}`
    );
    
    return data;
  } catch (error) {
    logTest('Query All Locations', false, error.message);
    return null;
  }
}

/**
 * Test 6: Query cases with joins
 */
async function testQueryCasesWithJoins() {
  console.log('--- Test 6: Query Cases with Joins ---');
  
  try {
    const { data, error } = await supabase
      .from('cases')
      .select(`
        case_id,
        case_count,
        date_reported,
        severity,
        diseases (name, category),
        locations (city, state_province, latitude, longitude)
      `)
      .eq('verified', true)
      .order('date_reported', { ascending: false });

    if (error) throw error;
    
    const summary = data.map(c => 
      `${c.diseases.name} in ${c.locations.city}: ${c.case_count} cases`
    ).join('\n   ');
    
    logTest(
      'Query Cases with Joins',
      data && data.length > 0,
      `Found ${data.length} case(s):\n   ${summary}`
    );
    
    return data;
  } catch (error) {
    logTest('Query Cases with Joins', false, error.message);
    return null;
  }
}

/**
 * Test 7: Query with filters (date range)
 */
async function testQueryWithFilters() {
  console.log('--- Test 7: Query with Date Filter ---');
  
  try {
    const { data, error } = await supabase
      .from('cases')
      .select(`
        case_id,
        case_count,
        date_reported,
        diseases (name),
        locations (city, state_province)
      `)
      .gte('date_reported', '2026-02-01')
      .lte('date_reported', '2026-02-16')
      .eq('verified', true);

    if (error) throw error;
    
    logTest(
      'Query with Date Filter',
      data !== null,
      `Found ${data.length} case(s) between Feb 1-16, 2026`
    );
    
    return data;
  } catch (error) {
    logTest('Query with Date Filter', false, error.message);
    return null;
  }
}

/**
 * Test 8: Query specific disease cases
 */
async function testQuerySpecificDisease() {
  console.log('--- Test 8: Query Specific Disease ---');
  
  try {
    const { data: diseases, error: diseaseError } = await supabase
      .from('diseases')
      .select('disease_id, name')
      .limit(1)
      .single();

    if (diseaseError) throw diseaseError;

    const { data, error } = await supabase
      .from('cases')
      .select(`
        case_count,
        date_reported,
        locations (city, state_province)
      `)
      .eq('disease_id', diseases.disease_id)
      .eq('verified', true);

    if (error) throw error;
    
    logTest(
      'Query Specific Disease',
      data !== null,
      `Found ${data.length} case(s) for ${diseases.name}`
    );
    
    return data;
  } catch (error) {
    logTest('Query Specific Disease', false, error.message);
    return null;
  }
}

/**
 * Test 9: Aggregate query (total cases by disease)
 */
async function testAggregateQuery() {
  console.log('--- Test 9: Aggregate Query (Total Cases) ---');
  
  try {
    const { data: cases, error } = await supabase
      .from('cases')
      .select(`
        case_count,
        diseases (name)
      `)
      .eq('verified', true);

    if (error) throw error;

    const aggregated = cases.reduce((acc, curr) => {
      const diseaseName = curr.diseases.name;
      if (!acc[diseaseName]) {
        acc[diseaseName] = 0;
      }
      acc[diseaseName] += curr.case_count;
      return acc;
    }, {});

    const summary = Object.entries(aggregated)
      .map(([disease, total]) => `${disease}: ${total} cases`)
      .join('\n   ');
    
    logTest(
      'Aggregate Query',
      Object.keys(aggregated).length > 0,
      `Total cases by disease:\n   ${summary}`
    );
    
    return aggregated;
  } catch (error) {
    logTest('Aggregate Query', false, error.message);
    return null;
  }
}

/**
 * Main test runner
 */
async function runAllTests() {
  console.log('==========================================');
  console.log('  FLUENCE DATABASE TESTS');
  console.log('  Testing Insert and Query Operations');
  console.log('==========================================\n');

  if (!supabaseUrl || !supabaseKey) {
    console.log('❌ ERROR: Missing Supabase credentials');
    console.log('Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env file\n');
    return;
  }

  console.log(`Connected to: ${supabaseUrl}\n`);

  const disease = await testInsertDisease();
  const location = await testInsertLocation();
  const caseRecord = await testInsertCase(
    disease?.disease_id, 
    location?.location_id
  );

  await testQueryDiseases();
  await testQueryLocations();
  await testQueryCasesWithJoins();
  await testQueryWithFilters();
  await testQuerySpecificDisease();
  await testAggregateQuery();

  console.log('==========================================');
  console.log('  TEST SUMMARY');
  console.log('==========================================');
  console.log(`Total Tests Run: ${testsRun}`);
  console.log(`✅ Passed: ${testsPassed}`);
  console.log(`❌ Failed: ${testsFailed}`);
  console.log(`Success Rate: ${((testsPassed / testsRun) * 100).toFixed(1)}%`);
  console.log('==========================================\n');

  if (testsFailed === 0) {
    console.log('🎉 All tests passed! Database is working correctly.\n');
  } else {
    console.log('⚠️  Some tests failed. Please review the errors above.\n');
  }
}

runAllTests().catch(console.error);