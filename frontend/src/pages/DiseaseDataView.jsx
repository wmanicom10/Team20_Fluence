import { useEffect, useMemo, useState } from 'react';
import DiseaseCard from '../components/DiseaseCard';
import DiseaseTable from '../components/DiseaseTable';

/**
 * DiseaseDataView Page Component
 * Displays disease-related data in a clear format with filtering options
 *
 * Features:
 * - Toggle between card and table view
 * - Filter by disease type
 * - Sort by various fields
 * - Display key metrics: disease name, location, case count, date
 * - Load and render live data from backend UI endpoints
 */
function DiseaseDataView() {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  const [diseaseTypes, setDiseaseTypes] = useState(['All Diseases']);
  const [diseaseData, setDiseaseData] = useState([]);
  const [selectedDisease, setSelectedDisease] = useState('All Diseases');
  const [sortBy, setSortBy] = useState('caseCount');
  const [sortOrder, setSortOrder] = useState('desc');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isActive = true;

    const loadDiseaseTypes = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/ui/disease-types`);
        const payload = await response.json().catch(() => ({}));

        if (!response.ok || payload?.status === 'error') {
          const message =
            payload?.error?.message ||
            payload?.message ||
            `Failed to load disease types (${response.status})`;
          throw new Error(message);
        }

        const fetchedTypes = Array.isArray(payload?.data) ? payload.data : [];
        const normalizedTypes = fetchedTypes.length > 0 ? fetchedTypes : ['All Diseases'];

        if (isActive) {
          setDiseaseTypes(normalizedTypes);
          setSelectedDisease((prev) => (normalizedTypes.includes(prev) ? prev : 'All Diseases'));
        }
      } catch (loadError) {
        if (isActive) {
          setError(loadError.message);
        }
      }
    };

    loadDiseaseTypes();

    return () => {
      isActive = false;
    };
  }, [apiBaseUrl]);

  useEffect(() => {
    let isActive = true;

    const loadDiseaseData = async () => {
      setIsLoading(true);
      setError('');

      try {
        const params = new URLSearchParams();
        if (selectedDisease && selectedDisease !== 'All Diseases') {
          params.set('disease', selectedDisease);
        }

        const endpoint = params.toString()
          ? `${apiBaseUrl}/api/ui/disease-data?${params.toString()}`
          : `${apiBaseUrl}/api/ui/disease-data`;

        const response = await fetch(endpoint);
        const payload = await response.json().catch(() => ({}));

        if (!response.ok || payload?.status === 'error') {
          const message =
            payload?.error?.message ||
            payload?.message ||
            `Failed to load dashboard data (${response.status})`;
          throw new Error(message);
        }

        if (isActive) {
          setDiseaseData(Array.isArray(payload?.data) ? payload.data : []);
        }
      } catch (loadError) {
        if (isActive) {
          setError(loadError.message);
          setDiseaseData([]);
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    loadDiseaseData();

    return () => {
      isActive = false;
    };
  }, [apiBaseUrl, selectedDisease]);

  const sortedData = useMemo(() => {
    const severityOrder = { Critical: 4, High: 3, Medium: 2, Low: 1 };

    return [...diseaseData].sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'caseCount':
          comparison = (a.caseCount || 0) - (b.caseCount || 0);
          break;
        case 'disease':
          comparison = String(a.disease || '').localeCompare(String(b.disease || ''));
          break;
        case 'date':
          comparison = new Date(a.date || 0) - new Date(b.date || 0);
          break;
        case 'severity':
          comparison = (severityOrder[a.severity] || 0) - (severityOrder[b.severity] || 0);
          break;
        default:
          comparison = 0;
      }

      return sortOrder === 'desc' ? -comparison : comparison;
    });
  }, [diseaseData, sortBy, sortOrder]);

  const totalCases = sortedData.reduce((sum, item) => sum + (item.caseCount || 0), 0);
  const totalNew24h = sortedData.reduce((sum, item) => sum + (item.newCases24h || 0), 0);
  const criticalCount = sortedData.filter((item) => item.severity === 'Critical').length;

  return (
    <div className="disease-data-view">
      <header className="page-header">
        <h1>Disease Data Dashboard</h1>
        <p>View and analyze disease surveillance data across regions</p>
      </header>

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
          <span className="stat-value">{sortedData.length}</span>
          <span className="stat-label">Regions</span>
        </div>
        <div className="stat-card critical">
          <span className="stat-value">{criticalCount}</span>
          <span className="stat-label">Critical</span>
        </div>
      </section>

      <section className="controls">
        <div className="control-group">
          <label htmlFor="disease-filter">Filter by Disease:</label>
          <select
            id="disease-filter"
            value={selectedDisease}
            onChange={(e) => setSelectedDisease(e.target.value)}
          >
            {diseaseTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
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
            {sortOrder === 'asc' ? 'Asc' : 'Desc'}
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

      <section className="data-display">
        {isLoading && <p className="dashboard-state">Loading dashboard data...</p>}

        {!isLoading && error && (
          <p className="dashboard-state dashboard-state-error">
            Unable to load dashboard data: {error}
          </p>
        )}

        {!isLoading && !error && sortedData.length === 0 && (
          <p className="dashboard-state">No disease data is available for this filter.</p>
        )}

        {!isLoading && !error && sortedData.length > 0 && viewMode === 'cards' ? (
          <div className="cards-grid">
            {sortedData.map((item) => (
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
        ) : null}

        {!isLoading && !error && sortedData.length > 0 && viewMode === 'table' ? (
          <DiseaseTable data={sortedData} />
        ) : null}
      </section>

      <footer className="data-footer">
        <p>
          <em>Note: Data shown is loaded from live backend API responses.</em>
        </p>
      </footer>
    </div>
  );
}

export default DiseaseDataView;

