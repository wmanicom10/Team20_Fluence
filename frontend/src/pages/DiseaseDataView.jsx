import { useState } from 'react';
import { mockDiseaseData, diseaseTypes } from '../data/mockDiseaseData';
import DiseaseCard from '../components/DiseaseCard';
import DiseaseTable from '../components/DiseaseTable';

/**
 * DiseaseDataView Page Component
 * Displays disease-related data in a clear format with filtering options
 * Uses mock data - no backend dependency required
 * 
 * Features:
 * - Toggle between card and table view
 * - Filter by disease type
 * - Sort by various fields
 * - Display key metrics: disease name, location, case count, date
 */
function DiseaseDataView() {
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  const [selectedDisease, setSelectedDisease] = useState('All Diseases');
  const [sortBy, setSortBy] = useState('caseCount');
  const [sortOrder, setSortOrder] = useState('desc');

  // Filter data based on selected disease
  const filteredData = mockDiseaseData.filter(item => {
    if (selectedDisease === 'All Diseases') return true;
    return item.disease === selectedDisease;
  });

  // Sort filtered data
  const sortedData = [...filteredData].sort((a, b) => {
    let comparison = 0;
    
    switch (sortBy) {
      case 'caseCount':
        comparison = a.caseCount - b.caseCount;
        break;
      case 'disease':
        comparison = a.disease.localeCompare(b.disease);
        break;
      case 'date':
        comparison = new Date(a.date) - new Date(b.date);
        break;
      case 'severity':
        const severityOrder = { Critical: 4, High: 3, Medium: 2, Low: 1 };
        comparison = severityOrder[a.severity] - severityOrder[b.severity];
        break;
      default:
        comparison = 0;
    }
    
    return sortOrder === 'desc' ? -comparison : comparison;
  });

  // Calculate summary statistics
  const totalCases = filteredData.reduce((sum, item) => sum + item.caseCount, 0);
  const totalNew24h = filteredData.reduce((sum, item) => sum + item.newCases24h, 0);
  const criticalCount = filteredData.filter(item => item.severity === 'Critical').length;

  return (
    <div className="disease-data-view">
      <header className="page-header">
        <h1>Disease Data Dashboard</h1>
        <p>View and analyze disease surveillance data across regions</p>
      </header>

      {/* Summary Statistics */}
      <section className="summary-stats">
        <div className="stat-card">
          <span className="stat-value">{totalCases.toLocaleString()}</span>
          <span className="stat-label">Total Cases</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{totalNew24h}</span>
          <span className="stat-label">New (24h)</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{filteredData.length}</span>
          <span className="stat-label">Regions</span>
        </div>
        <div className="stat-card critical">
          <span className="stat-value">{criticalCount}</span>
          <span className="stat-label">Critical</span>
        </div>
      </section>

      {/* Controls */}
      <section className="controls">
        <div className="control-group">
          <label htmlFor="disease-filter">Filter by Disease:</label>
          <select 
            id="disease-filter"
            value={selectedDisease} 
            onChange={(e) => setSelectedDisease(e.target.value)}
          >
            {diseaseTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="sort-by">Sort by:</label>
          <select 
            id="sort-by"
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="caseCount">Case Count</option>
            <option value="disease">Disease Name</option>
            <option value="date">Date</option>
            <option value="severity">Severity</option>
          </select>
          <button 
            className="sort-order-btn"
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
          >
            {sortOrder === 'asc' ? '↑ Asc' : '↓ Desc'}
          </button>
        </div>

        <div className="control-group view-toggle">
          <button 
            className={`view-btn ${viewMode === 'cards' ? 'active' : ''}`}
            onClick={() => setViewMode('cards')}
          >
            Cards
          </button>
          <button 
            className={`view-btn ${viewMode === 'table' ? 'active' : ''}`}
            onClick={() => setViewMode('table')}
          >
            Table
          </button>
        </div>
      </section>

      {/* Data Display */}
      <section className="data-display">
        {viewMode === 'cards' ? (
          <div className="cards-grid">
            {sortedData.map(item => (
              <DiseaseCard
                key={item.id}
                disease={item.disease}
                location={item.location}
                caseCount={item.caseCount}
                date={item.date}
                severity={item.severity}
                newCases24h={item.newCases24h}
                rateOfChange={item.rateOfChange}
              />
            ))}
          </div>
        ) : (
          <DiseaseTable data={sortedData} />
        )}
      </section>

      {/* Data Source Note */}
      <footer className="data-footer">
        <p>
          <em>Note: Currently displaying mock data for development purposes. 
          Live data integration with CDC and WHO APIs will be implemented in future sprints.</em>
        </p>
      </footer>
    </div>
  );
}

export default DiseaseDataView;
