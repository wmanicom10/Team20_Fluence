import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { mockDiseaseData, diseaseTypes } from '../data/mockDiseaseData';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix default marker icon issue with React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

/**
 * Hardcoded coordinates for sample locations
 * Maps city names from mockDiseaseData to lat/lng
 */
const locationCoords = {
  "New York, NY": { lat: 40.7128, lng: -74.0060 },
  "Los Angeles, CA": { lat: 34.0522, lng: -118.2437 },
  "Chicago, IL": { lat: 41.8781, lng: -87.6298 },
  "Houston, TX": { lat: 29.7604, lng: -95.3698 },
  "Phoenix, AZ": { lat: 33.4484, lng: -112.0740 },
  "Philadelphia, PA": { lat: 39.9526, lng: -75.1652 },
  "San Antonio, TX": { lat: 29.4241, lng: -98.4936 },
  "San Diego, CA": { lat: 32.7157, lng: -117.1611 },
  "Dallas, TX": { lat: 32.7767, lng: -96.7970 },
  "San Jose, CA": { lat: 37.3382, lng: -121.8863 },
};

/**
 * MapView Page Component
 * Displays disease data as markers on an interactive Leaflet map
 * Includes disease dropdown filter and date range selector
 * Uses hardcoded sample data - no backend dependency required
 */
function MapView() {
  const [selectedDisease, setSelectedDisease] = useState('All Diseases');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Center map on the US
  const mapCenter = [39.8283, -98.5795];
  const defaultZoom = 4;

  // Filter data based on disease selection and date range
  const filteredData = mockDiseaseData.filter(item => {
    // Disease filter
    if (selectedDisease !== 'All Diseases' && item.disease !== selectedDisease) {
      return false;
    }
    // Date range filter
    if (startDate && item.date < startDate) {
      return false;
    }
    if (endDate && item.date > endDate) {
      return false;
    }
    return true;
  });

  // Clear all filters
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

      {/* Filter Controls */}
      <section className="map-filters">
        <div className="filter-group">
          <label htmlFor="map-disease-filter">Disease:</label>
          <select
            id="map-disease-filter"
            value={selectedDisease}
            onChange={(e) => setSelectedDisease(e.target.value)}
          >
            {diseaseTypes.map(type => (
              <option key={type} value={type}>{type}</option>
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

        <span className="filter-count">
          Showing {filteredData.length} of {mockDiseaseData.length} reports
        </span>
      </section>

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

          {filteredData.map(item => {
            const coords = locationCoords[item.location];
            if (!coords) return null;

            return (
              <Marker key={item.id} position={[coords.lat, coords.lng]}>
                <Popup>
                  <strong>{item.disease}</strong><br />
                  {item.location}<br />
                  Cases: {item.caseCount.toLocaleString()}<br />
                  Severity: {item.severity}<br />
                  New (24h): {item.newCases24h}<br />
                  Date: {item.date}
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>

      <footer className="data-footer">
        <p>
          <em>Note: Currently displaying hardcoded sample data.
          Live data integration will be implemented in future sprints.</em>
        </p>
      </footer>
    </div>
  );
}

export default MapView;
