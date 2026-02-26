import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://rogzdnrmmsdlpxjbgtvj.supabase.co';
const supabaseKey = 'sb_publishable_yinNcPmYmUIaIGSpkNJCjQ_vPxrnSbZ';
const supabase = createClient(supabaseUrl, supabaseKey);

export async function filterCases({ diseaseName, diseaseId, dateFrom, dateTo, verifiedOnly = false } = {}) {
  let query = supabase
    .from('cases')
    .select(`
      case_id,
      case_count,
      date_reported,
      severity,
      verified,
      data_source,
      diseases ( disease_id, name, category, severity_level ),
      locations ( location_id, city, state_province, country, latitude, longitude )
    `);

  if (diseaseId) {
    query = query.eq('disease_id', diseaseId);
  } else if (diseaseName) {
    const { data: disease, error: diseaseErr } = await supabase
      .from('diseases')
      .select('disease_id')
      .ilike('name', diseaseName)
      .eq('is_active', true)
      .single();

    if (diseaseErr || !disease) {
      return { data: [], error: diseaseErr ?? new Error(`Disease "${diseaseName}" not found`) };
    }
    query = query.eq('disease_id', disease.disease_id);
  }

  if (dateFrom) query = query.gte('date_reported', dateFrom);
  if (dateTo)   query = query.lte('date_reported', dateTo);

  if (verifiedOnly) query = query.eq('verified', true);

  query = query.order('date_reported', { ascending: false });

  const { data, error } = await query;
  return { data: data ?? [], error };
}

export async function recentCasesByDisease(diseaseName, days = 30) {
  const dateFrom = new Date();
  dateFrom.setDate(dateFrom.getDate() - days);

  return filterCases({
    diseaseName,
    dateFrom: dateFrom.toISOString().split('T')[0],
    verifiedOnly: true,
  });
}

export async function casesByDateRange(dateFrom, dateTo) {
  return filterCases({ dateFrom, dateTo });
}


async function runTests() {
  console.log('=== Fluence Filter Query Tests ===\n');

  console.log('--- Test 1: COVID-19 cases from 2024-01-01 to 2024-06-30 ---');
  const { data: t1, error: e1 } = await filterCases({
    diseaseName: 'COVID-19',
    dateFrom: '2024-01-01',
    dateTo: '2024-06-30',
  });
  if (e1) console.error('Error:', e1.message);
  else    console.log(`Found ${t1.length} records:`, JSON.stringify(t1, null, 2));

  console.log('\n--- Test 2: Cases for disease_id = 3 ---');
  const { data: t2, error: e2 } = await filterCases({ diseaseId: 3 });
  if (e2) console.error('Error:', e2.message);
  else    console.log(`Found ${t2.length} records:`, JSON.stringify(t2, null, 2));

  console.log('\n--- Test 3: Verified COVID-19 cases in the last 30 days ---');
  const { data: t3, error: e3 } = await recentCasesByDisease('COVID-19', 30);
  if (e3) console.error('Error:', e3.message);
  else    console.log(`Found ${t3.length} records:`, JSON.stringify(t3, null, 2));

  console.log('\n--- Test 4: All cases from 2024-03-01 to 2024-03-31 ---');
  const { data: t4, error: e4 } = await casesByDateRange('2024-03-01', '2024-03-31');
  if (e4) console.error('Error:', e4.message);
  else    console.log(`Found ${t4.length} records:`, JSON.stringify(t4, null, 2));

  console.log('\n=== Tests complete ===');
}

runTests();