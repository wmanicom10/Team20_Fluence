/**
 * Mock Disease Data for Fluence Application
 * Used for frontend development and testing without backend dependency
 * 
 * Data structure aligns with expected backend schema:
 * - disease: Disease name (CDC classification)
 * - location: Geographic location (city, state)
 * - caseCount: Number of reported cases
 * - date: Date of report
 * - severity: Severity level (Low, Medium, High, Critical)
 * - newCases24h: New cases in last 24 hours
 * - rateOfChange: Percentage change from previous period
 */

export const mockDiseaseData = [
  {
    id: 1,
    disease: "Influenza A",
    location: "New York, NY",
    caseCount: 1245,
    date: "2026-02-15",
    severity: "High",
    newCases24h: 87,
    rateOfChange: 12.5
  },
  {
    id: 2,
    disease: "COVID-19",
    location: "Los Angeles, CA",
    caseCount: 892,
    date: "2026-02-15",
    severity: "Medium",
    newCases24h: 45,
    rateOfChange: -3.2
  },
  {
    id: 3,
    disease: "RSV",
    location: "Chicago, IL",
    caseCount: 523,
    date: "2026-02-15",
    severity: "Medium",
    newCases24h: 32,
    rateOfChange: 8.7
  },
  {
    id: 4,
    disease: "Norovirus",
    location: "Houston, TX",
    caseCount: 312,
    date: "2026-02-14",
    severity: "Low",
    newCases24h: 18,
    rateOfChange: 2.1
  },
  {
    id: 5,
    disease: "Influenza B",
    location: "Phoenix, AZ",
    caseCount: 198,
    date: "2026-02-15",
    severity: "Low",
    newCases24h: 12,
    rateOfChange: -1.5
  },
  {
    id: 6,
    disease: "Strep A",
    location: "Philadelphia, PA",
    caseCount: 156,
    date: "2026-02-15",
    severity: "Medium",
    newCases24h: 23,
    rateOfChange: 15.3
  },
  {
    id: 7,
    disease: "Measles",
    location: "San Antonio, TX",
    caseCount: 45,
    date: "2026-02-14",
    severity: "Critical",
    newCases24h: 8,
    rateOfChange: 28.6
  },
  {
    id: 8,
    disease: "Pertussis",
    location: "San Diego, CA",
    caseCount: 89,
    date: "2026-02-15",
    severity: "Medium",
    newCases24h: 5,
    rateOfChange: 4.2
  },
  {
    id: 9,
    disease: "Hepatitis A",
    location: "Dallas, TX",
    caseCount: 67,
    date: "2026-02-13",
    severity: "Low",
    newCases24h: 3,
    rateOfChange: -2.8
  },
  {
    id: 10,
    disease: "Tuberculosis",
    location: "San Jose, CA",
    caseCount: 34,
    date: "2026-02-15",
    severity: "High",
    newCases24h: 2,
    rateOfChange: 6.3
  }
];

/**
 * Disease type options for filtering
 */
export const diseaseTypes = [
  "All Diseases",
  "Influenza A",
  "Influenza B",
  "COVID-19",
  "RSV",
  "Norovirus",
  "Strep A",
  "Measles",
  "Pertussis",
  "Hepatitis A",
  "Tuberculosis"
];

/**
 * Severity levels for filtering and styling
 */
export const severityLevels = {
  Low: { color: "#28a745", label: "Low" },
  Medium: { color: "#ffc107", label: "Medium" },
  High: { color: "#fd7e14", label: "High" },
  Critical: { color: "#dc3545", label: "Critical" }
};

export const mockRawCasesData = mockDiseaseData.map(d => {
  const [city, state_province] = d.location.split(', ');
  const coords = {
    "New York": { lat: 40.71, lng: -74.00 },
    "Los Angeles": { lat: 34.05, lng: -118.24 },
    "Chicago": { lat: 41.87, lng: -87.62 },
    "Houston": { lat: 29.76, lng: -95.36 },
    "Phoenix": { lat: 33.44, lng: -112.07 },
    "Philadelphia": { lat: 39.95, lng: -75.16 },
    "San Antonio": { lat: 29.42, lng: -98.49 },
    "San Diego": { lat: 32.71, lng: -117.16 },
    "Dallas": { lat: 32.77, lng: -96.79 },
    "San Jose": { lat: 37.33, lng: -121.88 }
  };
  return {
    case_id: d.id,
    case_count: d.caseCount,
    severity: d.severity,
    date_reported: d.date,
    diseases: { name: d.disease },
    locations: {
      city,
      state_province,
      latitude: coords[city]?.lat || 0,
      longitude: coords[city]?.lng || 0
    }
  };
});
