import React, { useEffect, useRef, useState } from 'react';
import ReactDOMServer from 'react-dom/server';

import { MapContainer } from 'react-leaflet/MapContainer'
import { useMap, useMapEvents, useMapEvent } from 'react-leaflet/hooks'
import { GeoJSON } from 'react-leaflet/GeoJSON'
import { Marker } from 'react-leaflet/Marker'
import { Popup } from 'react-leaflet/Popup'
import { Tooltip } from 'react-leaflet/Tooltip'
import { TileLayer } from 'react-leaflet/TileLayer'
import { WMSTileLayer } from 'react-leaflet/WMSTileLayer'

import { GeoJsonObject, Feature, Geometry } from 'geojson';

import 'leaflet/dist/leaflet.css';
import 'leaflet-rotatedmarker';
import L from 'leaflet';

// Define the type for GeoJSON data
interface GeoJSONFeature {
  type: string;
  properties: {
      SHIP_ID?: string;
      ship_id?: string;
      RECPTN_DT?: string;
      SEQUENCE_ID?: number;
      SOG?: number;
      COG?: number;
      TYPE?: string;
      LEN_PRED?: number;
      TON?: number;
      dist?: number;
      sea_lv?: number;
      port_name?: string;
      angle?: number;
      MODE?: string;
  };
  geometry: {
      type: string;
      coordinates: number[] | number[][][];
  };
}

interface GeoJSONData {
  type: string;
  features: GeoJSONFeature[];
  vo?: GeoJsonObject;
  v?: GeoJsonObject;
}

interface VesselMapProps {
  geojsonData: GeoJSONData | null;
  tileLayerUrl: string;
  tileLayerAttribution: string;
}

// Fix the default icon issue with React Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

const vesselIcon = L.icon({
  iconUrl: '/vesselarrow.png', // Path to your icon
  iconSize: [50, 50], // Size of the icon
  iconAnchor: [25, 25], // Point of the icon which will correspond to marker's location
  popupAnchor: [0, -5] // Point from which the popup should open relative to the iconAnchor
});

const VesselMap: React.FC<VesselMapProps> = ({ geojsonData, tileLayerUrl, tileLayerAttribution }) => {

  useEffect(() => {
      console.log("GeoJSON Data Updated:", geojsonData);
  }, [geojsonData]);

  const formatMode = (mode: string): string => {
    return mode
      .toLowerCase()
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const renderMarkerPopup = (feature: GeoJSONFeature) => {

    const hasMode = feature.properties.MODE !== undefined;

      return (
          <Popup>
              <div>
                  <strong>ID:</strong> {feature.properties.SHIP_ID || feature.properties.ship_id}<br />
                  <strong>LA:</strong> {Array.isArray(feature.geometry.coordinates[0]) ? feature.geometry.coordinates[0][1] : feature.geometry.coordinates[1]}<br />
                  <strong>LO:</strong> {Array.isArray(feature.geometry.coordinates[0]) ? feature.geometry.coordinates[0][0] : feature.geometry.coordinates[0]}
                  {hasMode && (
                    <>
                      <br />
                      <strong>Encounter Mode:</strong> {formatMode(feature.properties.MODE!)}
                    </>
                  )}
              </div>
          </Popup>
      );
  };

  return (
      <MapContainer center={[35.9078, 127.7669]} zoom={7} className="h-full w-full">
          <TileLayer
              // url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              // attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
              url={tileLayerUrl}
              attribution={tileLayerAttribution}
          />

          {geojsonData && geojsonData.features && geojsonData.features.map((feature, idx) => (
              feature.geometry.type === 'Point' ? (
                <Marker
                  key={idx}
                  position={[
                      feature.geometry.coordinates[1] as number,
                      feature.geometry.coordinates[0] as number
                  ]}
                  icon={vesselIcon} // Use the custom icon here
                  rotationAngle={feature.properties.COG || 0} // Rotate according to COG
                  rotationOrigin="center"
                >
                  {renderMarkerPopup(feature)}
                </Marker>
              ) : (
                  <GeoJSON key={idx} data={feature as GeoJsonObject} />
              )
          ))}

          {geojsonData?.vo && (
              <GeoJSON data={geojsonData.vo} style={{ color: 'red' }} />
          )}
          {geojsonData?.v && (
              <GeoJSON data={geojsonData.v} style={{ color: 'blue' }} />
          )}
      </MapContainer>
  );
};

export default VesselMap;