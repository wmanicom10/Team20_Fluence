import { severityLevels } from '../data/mockDiseaseData';

/**
 * DiseaseTable Component
 * Reusable table component for displaying disease data in tabular format
 * 
 * Props:
 * - data: Array of disease objects containing:
 *   - id: number - Unique identifier
 *   - disease: string - Name of the disease
 *   - location: string - Geographic location
 *   - caseCount: number - Total number of cases
 *   - date: string - Date of report
 *   - severity: string - Severity level
 *   - newCases24h: number - New cases in last 24 hours
 *   - rateOfChange: number - Percentage change
 */
function DiseaseTable({ data }) {
  if (!data || data.length === 0) {
    return <p className="no-data">No disease data available.</p>;
  }

  return (
    <div className="table-container">
      <table className="disease-table">
        <thead>
          <tr>
            <th>Disease</th>
            <th>Location</th>
            <th>Case Count</th>
            <th>New (24h)</th>
            <th>Trend</th>
            <th>Severity</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => {
            const severityStyle = severityLevels[item.severity] || severityLevels.Low;
            const isIncreasing = item.rateOfChange > 0;
            
            return (
              <tr key={item.id}>
                <td className="disease-name">{item.disease}</td>
                <td>{item.location}</td>
                <td className="case-count">{item.caseCount.toLocaleString()}</td>
                <td>{item.newCases24h}</td>
                <td className={`trend ${isIncreasing ? 'increasing' : 'decreasing'}`}>
                  {isIncreasing ? '↑' : '↓'} {Math.abs(item.rateOfChange)}%
                </td>
                <td>
                  <span 
                    className="severity-badge"
                    style={{ backgroundColor: severityStyle.color }}
                  >
                    {item.severity}
                  </span>
                </td>
                <td>{new Date(item.date).toLocaleDateString()}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default DiseaseTable;
