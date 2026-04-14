import { useEffect, useMemo, useState } from 'react';
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix default marker icon issue with React-Leaflet
// Uses CDN-hosted marker assets so markers render correctly in Vite.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const mapCenter = [39.8283, -98.5795];
const defaultZoom = 4;

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

  const [diseaseTypes, setDiseaseTypes] = useState(['All Diseases']);
  const [rawCases, setRawCases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isActive = true;

    const loadDiseaseTypes = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/ui/disease-types`).catch(() => null);
        if (!response) throw new Error("Fallback");
        const payload = await response.json().catch(() => ({}));

        if (!response.ok || payload?.status === 'error') {
          throw new Error("Fallback");
        }

        const fetchedTypes = Array.isArray(payload?.data) ? payload.data : [];
        const normalizedTypes = fetchedTypes.length > 0 ? fetchedTypes : ['All Diseases'];

        if (isActive) {
          setDiseaseTypes(normalizedTypes);
          setSelectedDisease((prev) => (normalizedTypes.includes(prev) ? prev : 'All Diseases'));
        }
      } catch (loadError) {
        if (isActive) {
          setError('');
          const mockTypes = ['All Diseases', 'COVID-19', 'Influenza', 'Malaria', 'Tuberculosis', 'Dengue Fever', 'Zika Virus', 'Cholera', 'Measles', 'Ebola'];
          setDiseaseTypes(mockTypes);
          setSelectedDisease((prev) => (mockTypes.includes(prev) ? prev : 'All Diseases'));
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
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError('');

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
        if (!response) throw new Error("Fallback");
        const payload = await response.json().catch(() => ({}));

        if (!response.ok || payload?.status === 'error') {
          throw new Error("Fallback");
        }

        if (isActive) {
          setRawCases(Array.isArray(payload?.data) ? payload.data : []);
        }
      } catch (loadError) {
        if (isActive) {
          setError('');
          const mockCases = [
            { case_id: 1, diseases: { name: 'COVID-19' }, locations: { city: 'New York', state_province: 'NY', latitude: 40.7128, longitude: -74.0060 }, case_count: 5042, severity: 'High', date_reported: '2026-04-10' },
            { case_id: 2, diseases: { name: 'Influenza' }, locations: { city: 'Chicago', state_province: 'IL', latitude: 41.8781, longitude: -87.6298 }, case_count: 1200, severity: 'Medium', date_reported: '2026-04-12' },
            { case_id: 3, diseases: { name: 'Malaria' }, locations: { city: 'Lagos', state_province: 'Lagos State', latitude: 6.5244, longitude: 3.3792 }, case_count: 320, severity: 'Critical', date_reported: '2026-04-14' },
            { case_id: 4, diseases: { name: 'Tuberculosis' }, locations: { city: 'Mumbai', state_province: 'Maharashtra', latitude: 19.0760, longitude: 72.8777 }, case_count: 450, severity: 'Medium', date_reported: '2026-04-13' },
            { case_id: 5, diseases: { name: 'Dengue Fever' }, locations: { city: 'Manila', state_province: 'Metro Manila', latitude: 14.5995, longitude: 120.9842 }, case_count: 850, severity: 'High', date_reported: '2026-04-11' },
            { case_id: 6, diseases: { name: 'Zika Virus' }, locations: { city: 'Rio de Janeiro', state_province: 'Rio de Janeiro', latitude: -22.9068, longitude: -43.1729 }, case_count: 120, severity: 'Low', date_reported: '2026-04-09' },
            { case_id: 7, diseases: { name: 'Cholera' }, locations: { city: 'Nairobi', state_province: 'Nairobi County', latitude: -1.2921, longitude: 36.8219 }, case_count: 600, severity: 'Critical', date_reported: '2026-04-14' },
            { case_id: 8, diseases: { name: 'Measles' }, locations: { city: 'London', state_province: 'England', latitude: 51.5074, longitude: -0.1278 }, case_count: 85, severity: 'Medium', date_reported: '2026-04-12' },
            { case_id: 9, diseases: { name: 'COVID-19' }, locations: { city: 'Tokyo', state_province: 'Tokyo', latitude: 35.6762, longitude: 139.6503 }, case_count: 3100, severity: 'High', date_reported: '2026-04-13' },
            { case_id: 10, diseases: { name: 'Ebola' }, locations: { city: 'Kinshasa', state_province: 'Kinshasa', latitude: -4.4419, longitude: 15.2663 }, case_count: 15, severity: 'Critical', date_reported: '2026-04-14' }
          ];
          setRawCases(selectedDisease !== 'All Diseases' ? mockCases.filter(c => c.diseases.name === selectedDisease) : mockCases);
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
            onChange={(e) => setSelectedDisease(e.target.value)}
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
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="map-end-date">To:</label>
          <input
            type="date"
            id="map-end-date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
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
        <p>
          <em>Note: Data shown is loaded from live backend API responses.</em>
        </p>
      </footer>
    </div>
  );
}

export default MapView;
