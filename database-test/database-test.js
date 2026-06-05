import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://qvwnvypywdxntemfrfmr.supabase.co'
const supabaseKey = 'sb_publishable_b1bZ1OSc0K_XkjA-uW_hIg_vACuXq2q'
const supabase = createClient(supabaseUrl, supabaseKey)

async function simpleTest() {
  console.log('Testing Supabase connection...\n')
  
  const { data, error } = await supabase
    .from('test')
    .select('*')
  
  if (error) {
    console.error('Error:', error.message)
  } else {
    console.log('Success! Data from test table:')
    console.log(data)
  }
}

simpleTest()