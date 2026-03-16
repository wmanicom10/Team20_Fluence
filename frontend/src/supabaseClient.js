import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://rogzdnrmmsdlpxjbgtvj.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJvZ3pkbnJtbXNkbHB4amJndHZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzExNjE3NDEsImV4cCI6MjA4NjczNzc0MX0.Pc1Et0GbAFPSXQvZSrpZMK0G5wq2cpP-y2g-YvFekcY';
export const supabase = createClient(supabaseUrl, supabaseKey);