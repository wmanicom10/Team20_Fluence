import { useEffect, useMemo, useState } from 'react';
import DiseaseCard from '../components/DiseaseCard';
import DiseaseTable from '../components/DiseaseTable';
import AiRiskSummary from '../components/AiRiskSummary';
import { mockDiseaseData, diseaseTypes as mockDiseaseTypes } from '../data/mockDiseaseData';

const DEFAULT_DISEASE_TYPES = ['All Diseases'];

const getErrorMessage = (payload, fallbackMessage) => {
  if (payload?.error?.message) {
    return payload.error.message;
  }

  if (payload?.message) {
    return payload.message;
  }

  return fallbackMessage;
};

const toCdcPathogen = (selectedDisease) => {
  if (!selectedDisease || selectedDisease === 'All Diseases') {
    return '';
  }

  if (selectedDisease === 'COVID-19') {
    return 'COVID';
  }

  if (selectedDisease === 'Influenza') {
    return 'Influenza';
  }

  if (selectedDisease === 'RSV') {
    return 'RSV';
  }

  return null;
};

/**
 * DiseaseDataView Page Component
 * Displays disease-related data in a clear format with filtering options.
 */
function DiseaseDataView() {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

  const [viewMode, setViewMode] = useState('cards');
  const [diseaseTypes, setDiseaseTypes] = useState(DEFAULT_DISEASE_TYPES);
  const [diseaseData, setDiseaseData] = useState([]);
  const [selectedDisease, setSelectedDisease] = useState('All Diseases');
  const [sortBy, setSortBy] = useState('caseCount');
  const [sortOrder, setSortOrder] = useState('desc');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [dataSource, setDataSource] = useState('live');
  const [cdcFeed, setCdcFeed] = useState([]);
  const [cdcLoading, setCdcLoading] = useState(true);
  const [cdcError, setCdcError] = useState('');

  useEffect(() => {
    let isActive = true;

    const loadDiseaseTypes = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/ui/disease-types`).catch(() => null);
        if (!response) {
          throw new Error('Network request failed');
        }

        const payload = await response.json().catch(() => ({}));
        if (!response.ok || payload?.status === 'error') {
          throw new Error(getErrorMessage(payload, 'Failed to load disease filters.'));
        }

        const fetchedTypes = Array.isArray(payload?.data) ? payload.data : [];
        const normalizedTypes = fetchedTypes.length > 0 ? fetchedTypes : DEFAULT_DISEASE_TYPES;

        if (isActive) {
          setDiseaseTypes(normalizedTypes);
          setSelectedDisease((current) => (normalizedTypes.includes(current) ? current : 'All Diseases'));
        }
      } catch (loadError) {
        if (isActive) {
          setDiseaseTypes(mockDiseaseTypes);
          setSelectedDisease((current) => (mockDiseaseTypes.includes(current) ? current : 'All Diseases'));
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
      setDataSource('live');

      try {
        const params = new URLSearchParams();
        if (selectedDisease && selectedDisease !== 'All Diseases') {
          params.set('disease', selectedDisease);
        }

        const endpoint = params.toString()
          ? `${apiBaseUrl}/api/ui/disease-data?${params.toString()}`
          : `${apiBaseUrl}/api/ui/disease-data`;

        const response = await fetch(endpoint).catch(() => null);
        if (!response) {
          throw new Error('Network request failed');
        }

        const payload = await response.json().catch(() => ({}));
        if (!response.ok || payload?.status === 'error') {
          throw new Error(getErrorMessage(payload, 'Failed to load dashboard data.'));
        }

        if (isActive) {
          setDiseaseData(Array.isArray(payload?.data) ? payload.data : []);
          setDataSource('live');
        }
      } catch (loadError) {
        if (isActive) {
          let fallbackData = mockDiseaseData;
          if (selectedDisease && selectedDisease !== 'All Diseases') {
            fallbackData = mockDiseaseData.filter(d => d.disease === selectedDisease);
          }
          setDiseaseData(fallbackData);
          setDataSource('mock');
          setError('');
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

  useEffect(() => {
    let isActive = true;

    const loadCdcFeed = async () => {
      const pathogen = toCdcPathogen(selectedDisease);
      if (pathogen === null) {
        setCdcFeed([]);
        setCdcError('');
        setCdcLoading(false);
        return;
      }

      setCdcLoading(true);
      setCdcError('');

      try {
        const params = new URLSearchParams({ limit: '9' });
        if (pathogen) {
          params.set('pathogen', pathogen);
        }

        const response = await fetch(`${apiBaseUrl}/api/external/cdc/respiratory-daily?${params.toString()}`).catch(() => null);
        if (!response) {
          throw new Error('Network request failed');
        }

        const payload = await response.json().catch(() => ({}));
        if (!response.ok || payload?.status === 'error') {
          throw new Error(getErrorMessage(payload, 'Failed to load CDC respiratory feed.'));
        }

        if (isActive) {
          setCdcFeed(Array.isArray(payload?.data?.rows) ? payload.data.rows : []);
        }
      } catch (loadError) {
        if (isActive) {
          setCdcFeed([]);
          setCdcError(loadError.message || 'Failed to load CDC respiratory feed.');
        }
      } finally {
        if (isActive) {
          setCdcLoading(false);
        }
      }
    };

    loadCdcFeed();

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
        <div className="section-kicker">
          <span className="section-kicker-badge">Fluence Reports</span>
          <p>Collected and verified case reports stored in the Fluence platform.</p>
        </div>
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
        <AiRiskSummary apiBaseUrl={apiBaseUrl} disease={selectedDisease} />
      </section>

      <section className="controls">
        <div className="control-group">
          <label htmlFor="disease-filter">Filter by Disease:</label>
          <select
            id="disease-filter"
            value={selectedDisease}
            onChange={(event) => setSelectedDisease(event.target.value)}
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
            onChange={(event) => setSortBy(event.target.value)}
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

      <section className="external-feed-section">
        <div className="external-feed-header">
          <h2>CDC Respiratory Feed</h2>
          <p>
            Official CDC NSSP respiratory surveillance data shown alongside Fluence case reports.
          </p>
        </div>

        {cdcLoading && <p className="dashboard-state">Loading CDC respiratory feed...</p>}

        {!cdcLoading && cdcError && (
          <p className="dashboard-state dashboard-state-error">
            Unable to load CDC respiratory feed: {cdcError}
          </p>
        )}

        {!cdcLoading && !cdcError && cdcFeed.length === 0 && (
          <p className="dashboard-state">
            No CDC respiratory feed entries are available for this disease filter.
          </p>
        )}

        {!cdcLoading && !cdcError && cdcFeed.length > 0 ? (
          <div className="cards-grid">
            {cdcFeed.map((item) => (
              <article key={item.id} className="disease-card cdc-feed-card">
                <div className="card-header">
                  <div>
                    <h3 className="disease-name">{item.disease}</h3>
                    <p className="cdc-source-label">{item.source}</p>
                  </div>
                  <span className={`severity-badge severity-badge-${String(item.severity).toLowerCase()}`}>
                    {item.severity}
                  </span>
                </div>

                <div className="card-body">
                  <div className="card-row">
                    <span className="label">Location:</span>
                    <span className="value">{item.location}</span>
                  </div>
                  <div className="card-row">
                    <span className="label">ED Visits %:</span>
                    <span className="value case-count">{item.percentVisits}%</span>
                  </div>
                  <div className="card-row">
                    <span className="label">Previous Day %:</span>
                    <span className="value">{item.previousPercentVisits}%</span>
                  </div>
                  <div className="card-row">
                    <span className="label">Change (1d):</span>
                    <span className={`value trend ${item.changePoints > 0 ? 'increasing' : 'decreasing'}`}>
                      {item.changePoints > 0 ? '+' : ''}{item.changePoints} pts
                    </span>
                  </div>
                  <div className="card-row">
                    <span className="label">Reported:</span>
                    <span className="value date">{new Date(item.date).toLocaleDateString()}</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>

      <footer className="data-footer">
        <p className={dataSource === 'live' ? 'data-source-live' : 'data-source-unavailable'}>
          <em>
            {dataSource === 'live'
              ? 'Fluence Reports source: live backend API responses.'
              : dataSource === 'mock'
                ? 'Live backend data is currently unavailable. Showing mock data for demonstration.'
                : 'Live backend data is currently unavailable. Check the backend server and Supabase environment variables.'}
          </em>
        </p>
      </footer>
    </div>
  );
}

export default DiseaseDataView;
