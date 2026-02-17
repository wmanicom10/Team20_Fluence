import { severityLevels } from '../data/mockDiseaseData';

/**
 * DiseaseCard Component
 * Reusable card component for displaying individual disease case information
 * 
 * Props:
 * - disease: string - Name of the disease
 * - location: string - Geographic location
 * - caseCount: number - Total number of cases
 * - date: string - Date of report
 * - severity: string - Severity level (Low, Medium, High, Critical)
 * - newCases24h: number - New cases in last 24 hours
 * - rateOfChange: number - Percentage change from previous period
 */
function DiseaseCard({ 
  disease, 
  location, 
  caseCount, 
  date, 
  severity, 
  newCases24h, 
  rateOfChange 
}) {
  const severityStyle = severityLevels[severity] || severityLevels.Low;
  const isIncreasing = rateOfChange > 0;

  return (
    <div className="disease-card">
      <div className="card-header">
        <h3 className="disease-name">{disease}</h3>
        <span 
          className="severity-badge"
          style={{ backgroundColor: severityStyle.color }}
        >
          {severity}
        </span>
      </div>
      
      <div className="card-body">
        <div className="card-row">
          <span className="label">Location:</span>
          <span className="value">{location}</span>
        </div>
        
        <div className="card-row">
          <span className="label">Total Cases:</span>
          <span className="value case-count">{caseCount.toLocaleString()}</span>
        </div>
        
        <div className="card-row">
          <span className="label">New (24h):</span>
          <span className="value">{newCases24h}</span>
        </div>
        
        <div className="card-row">
          <span className="label">Trend:</span>
          <span className={`value trend ${isIncreasing ? 'increasing' : 'decreasing'}`}>
            {isIncreasing ? '↑' : '↓'} {Math.abs(rateOfChange)}%
          </span>
        </div>
        
        <div className="card-row">
          <span className="label">Reported:</span>
          <span className="value date">{new Date(date).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
}

export default DiseaseCard;
