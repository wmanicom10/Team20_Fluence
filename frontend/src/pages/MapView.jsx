import { useEffect, useMemo, useState } from 'react';
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

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

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const mapCenter = [20.0, 0.0];
const defaultZoom = 2;

const getNestedObject = (value) => {
  if (Array.isArray(value)) {
    return value[0] || {};
  }

  if (value && typeof value === 'object') {
    return value;
  }

  return {};
};

function MapView() {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

  const [selectedDisease, setSelectedDisease] = useState('All Diseases');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [diseaseTypes, setDiseaseTypes] = useState(DEFAULT_DISEASE_TYPES);
  const [rawCases, setRawCases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [dataSource, setDataSource] = useState('live');

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
          setDiseaseTypes(DEFAULT_DISEASE_TYPES);
          setSelectedDisease('All Diseases');
          setError((currentError) => currentError || loadError.message || 'Failed to load disease filters.');
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

    const loadCases = async () => {
      if (startDate && endDate && startDate > endDate) {
        setError('Start date cannot be later than end date.');
        setRawCases([]);
        setDataSource('unavailable');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError('');
      setDataSource('live');

      try {
        const params = new URLSearchParams({ verified_only: 'true' });

        if (selectedDisease && selectedDisease !== 'All Diseases') {
          params.set('disease_name', selectedDisease);
        }

        if (startDate) {
          params.set('date_from', startDate);
        }

        if (endDate) {
          params.set('date_to', endDate);
        }

        const response = await fetch(`${apiBaseUrl}/api/cases?${params.toString()}`).catch(() => null);
        if (!response) {
          throw new Error('Network request failed');
        }

        const payload = await response.json().catch(() => ({}));
        if (!response.ok || payload?.status === 'error') {
          throw new Error(getErrorMessage(payload, 'Failed to load map data.'));
        }

        if (isActive) {
          setRawCases(Array.isArray(payload?.data) ? payload.data : []);
          setDataSource('live');
        }
      } catch (loadError) {
        if (isActive) {
          setRawCases([]);
          setDataSource('unavailable');
          setError(loadError.message || 'Failed to load map data.');
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    loadCases();

    return () => {
      isActive = false;
    };
  }, [apiBaseUrl, selectedDisease, startDate, endDate]);

  const markerData = useMemo(() => {
    return rawCases
      .map((item) => {
        const disease = getNestedObject(item?.diseases);
        const location = getNestedObject(item?.locations);

        const city = location?.city || 'Unknown';
        const state = location?.state_province || '';
        const lat = Number(location?.latitude);
        const lng = Number(location?.longitude);

        if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
          return null;
        }

        return {
          id: item?.case_id,
          disease: disease?.name || 'Unknown',
          locationLabel: state ? `${city}, ${state}` : city,
          caseCount: Number(item?.case_count || 0),
          severity: item?.severity || 'Unknown',
          date: item?.date_reported || '',
          lat,
          lng,
        };
      })
      .filter(Boolean);
  }, [rawCases]);

  const handleClearFilters = () => {
    setSelectedDisease('All Diseases');
    setStartDate('');
    setEndDate('');
  };

  return (
    <div className="map-view">
      <header className="page-header">
        <h1>Disease Map</h1>
        <p>Geographic view of disease surveillance data</p>
      </header>

      <section className="map-filters">
        <div className="filter-group">
          <label htmlFor="map-disease-filter">Disease:</label>
          <select
            id="map-disease-filter"
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

        <div className="filter-group">
          <label htmlFor="map-start-date">From:</label>
          <input
            type="date"
            id="map-start-date"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="map-end-date">To:</label>
          <input
            type="date"
            id="map-end-date"
            value={endDate}
            onChange={(event) => setEndDate(event.target.value)}
          />
        </div>

        <button className="clear-filters-btn" onClick={handleClearFilters}>
          Clear Filters
        </button>

        <span className="filter-count">Showing {markerData.length} reports on map</span>
      </section>

      {isLoading && <p className="dashboard-state">Loading map data...</p>}
      {!isLoading && error && (
        <p className="dashboard-state dashboard-state-error">Unable to load map data: {error}</p>
      )}
      {!isLoading && !error && markerData.length === 0 && (
        <p className="dashboard-state">No map data available for the selected filters.</p>
      )}

      <div className="map-container" style={{ height: '600px', width: '100%' }}>
        <MapContainer
          center={mapCenter}
          zoom={defaultZoom}
          style={{ height: '100%', width: '100%', borderRadius: '8px' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {!isLoading && !error &&
            markerData.map((item) => (
              <Marker key={item.id} position={[item.lat, item.lng]}>
                <Popup>
                  <strong>{item.disease}</strong>
                  <br />
                  {item.locationLabel}
                  <br />
                  Cases: {item.caseCount.toLocaleString()}
                  <br />
                  Severity: {item.severity}
                  <br />
                  Date: {item.date || 'N/A'}
                </Popup>
              </Marker>
            ))}
        </MapContainer>
      </div>

      <footer className="data-footer">
        <p className={dataSource === 'live' ? 'data-source-live' : 'data-source-unavailable'}>
          <em>
            {dataSource === 'live'
              ? 'Data source: live backend API responses.'
              : 'Live backend data is currently unavailable. Check the backend server and Supabase environment variables.'}
          </em>
        </p>
      </footer>
    </div>
  );
}

export default MapView;
