'use client';
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

import dynamic from 'next/dynamic';

import { debounce } from 'lodash';

// Use dynamic import for ShipMap to disable SSR
const VesselMap = dynamic(() => import('./VesselMap'), { ssr: false });

const TestComp = () => {
    
    const [shipType, setShipType] = useState('');
    const [shipId, setShipId] = useState('');
    const [selectedTsIds, setSelectedTsIds] = useState<string[]>([]);
    const [dateTime, setDateTime] = useState<Date | null>(null);
    const [timeLength, setTimeLength] = useState('');
    const [shipIds, setShipIds] = useState<string[]>([]);
    const [calculationResult, setCalculationResult] = useState<number[]>([0, 0, 0, 0, 0]);
    const [geojsonData, setGeojsonData] = useState<any>(null);
    const [isResultUpdated, setIsResultUpdated] = useState(false);

    // Ref to prevent initial fetch on mount
    const initialRender = useRef(true);

    // Update ship IDs based on selected ship type
    useEffect(() => {
        const fetchShipIds = debounce(async () => {
            if (shipType) {
                try {
                    const response = await axios.get('http://127.0.0.1:8080/get_ship_ids', { params: { shipType } });
                    console.log("Ship IDs fetched:", response.data);  // Debugging print
                    setShipIds(response.data);
                } catch (error) {
                    console.error("Error fetching ship IDs:", error);
                }
            } else {
                setShipIds([]);
            }
        }, 300); // Wait 300ms before making the request
        if (initialRender.current) {
            initialRender.current = false;
        } else {
            fetchShipIds();
        }
    }, [shipType]);

    const handleTimeLengthChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        if (parseInt(value) > 0) {
            setTimeLength(value);
        } else {
            setTimeLength('');
        }
    };

    const debouncedSetSelectedTsIds = debounce((updatedIds) => {
        setSelectedTsIds(updatedIds);
    }, 300);

    const handleTsIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        console.log("Target Ship IDs:", value);  // Debugging print

        setSelectedTsIds((prevSelected) =>
            prevSelected.includes(value)
                ? prevSelected.filter((id) => id !== value)
                : [...prevSelected, value]
        );
    };

    const handleDisplay = async () => {
        if (!dateTime) {
            console.error("No datetime selected.");
            return;
        }

        // Convert local datetime to UTC before sending it to the backend
        const utcDateTime = new Date(dateTime.getTime() - (dateTime.getTimezoneOffset() * 60000)).toISOString();

        try {
            const response = await axios.get('http://127.0.0.1:8080/load_geojson_data_selected', { 
                params: { 
                    shipType, 
                    datetime: utcDateTime 
                } 
            });
            console.log("fetching GeoJSON data");
            
            if (response.data) {
                setGeojsonData(response.data);  // Set the fetched GeoJSON data to state
                console.log("GeoJSON data set:");
                console.log(response.data);
            } else {
                console.log("No data received from backend.");
            }
        } catch (error) {
            console.error("Error fetching GeoJSON data:", error);
        }
    };

    const handleCheckShipDomain = async () => {
        if (!dateTime) {
            console.error("No datetime selected.");
            return;
        }

        // Convert local datetime to UTC before sending it to the backend
        const utcDateTime = new Date(dateTime.getTime() - (dateTime.getTimezoneOffset() * 60000)).toISOString();
        
        try {
            const response = await axios.post('http://127.0.0.1:8080/os_domain', {
                shipType,
                shipId,
                datetime: utcDateTime,
                timeLength,
            });
            console.log("OS Calculation result:", response.data);

            if (response.data) {
                setGeojsonData(response.data);
            } else {
                console.log("No data received from backend.");
            }
        } catch (error) {
            console.error("Error fetching ship domain data:", error);
        }
    
    }

    const handleCollisionRisk = async () => {
        if (!dateTime) {
            console.error("No datetime selected.");
            return;
        }

        // Convert local datetime to UTC before sending it to the backend
        const utcDateTime = new Date(dateTime.getTime() - (dateTime.getTimezoneOffset() * 60000)).toISOString();

        try {
            const response = await axios.post('http://127.0.0.1:8080/computation', {
                shipType,
                shipId,
                selectedTsIds,
                datetime: utcDateTime,
                timeLength,
            });
            console.log("Computation result:", response.data);
            
            if (response.data) {
                setCalculationResult(response.data);  // Set the fetched GeoJSON data to state
                console.log("Calculation Result set:");
                console.log(response.data);
                setIsResultUpdated(true); // Set flag to true when result is updated

                // Fetch GeoJSON data for VO and V regions
                const voResponse = await axios.post('http://127.0.0.1:8080/computation_vo', {
                    shipType,
                    selectedTsIds,
                    datetime: utcDateTime,
                    timeLength,
                });

                const vResponse = await axios.post('http://127.0.0.1:8080/computation_v', {
                    shipType,
                    shipId,
                    datetime: utcDateTime,
                    timeLength,
                });

                console.log("VO Region Data:", voResponse.data);
                console.log("V Region Data:", vResponse.data);
                
                setGeojsonData({
                    vo: voResponse.data,
                    v: vResponse.data,
                });
                console.log("VO & V region data set")

            } else {
                console.log("No data received from backend.");
            }
        } catch (error) {
            console.error("Error in calculation process:", error);
        }
    };
    
    // OSM Humanitarian Layer
    const osmTileLayer = {
        // url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        // attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        url: "https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/" target="_blank">Humanitarian OpenStreetMap Team</a> hosted by <a href="https://openstreetmap.fr/" target="_blank">OpenStreetMap France</a>'
    };

    // const esriTileLayer = {
    //     url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    //     attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    // };

    const usgsTileLayer = {
        url: "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}",
        attribution: 'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
    };

    const [currentTileLayer, setCurrentTileLayer] = useState(osmTileLayer);

    // const toggleTileLayer = () => {
    //     setCurrentTileLayer((prev) => prev.url === esriTileLayer.url ? osmTileLayer : esriTileLayer);
    // };

    const toggleTileLayer = () => {
        setCurrentTileLayer((prev) => prev.url === usgsTileLayer.url ? osmTileLayer : usgsTileLayer);
    };

    return (
        <div className="flex flex-row items-start justify-start min-h-screen w-full mt-4 space-x-4">
            <div className="h-[80vh] flex flex-col justify-around space-y-6 p-4 bg-primary-content rounded-lg shadow-md z-10 relative w-1/4">

                <select className="select select-bordered select-secondary w-full" value={shipType} onChange={(e) => setShipType(e.target.value)}>
                    <option disabled value="">Select Ship Type</option>
                    <option value="cargo">Cargo</option>
                    <option value="passenger">Passenger</option>
                    {/* Add more ship types as needed */}
                </select>

                <DatePicker
                    selected={dateTime}
                    onChange={(date) => setDateTime(date as Date)} // Type assertion
                    showTimeSelect
                    timeFormat="HH:mm"
                    timeIntervals={10}
                    dateFormat="yyyy-MM-dd'T'HH:mm:ss"
                    className="input input-bordered input-secondary w-full"
                    placeholderText="Select Date and Time"
                />

                <button className="btn btn-primary mt-4" onClick={handleDisplay}>Display Vessels</button>

                <select className="select select-bordered select-secondary w-full" value={shipId} onChange={(e) => setShipId(e.target.value)}>
                    <option disabled value="">Select OS (Own Ship) ID</option>
                    {shipIds && shipIds.map((id) => (
                        <option key={id} value={id}>{id}</option>
                    ))}
                </select>

                <div className="dropdown dropdown-hover w-full">
                    <label tabIndex={0} className="btn btn-outline btn-secondary w-full">Select TS (Target Ship) IDs</label>
                    <ul tabIndex={0} className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-full max-h-60 overflow-y-auto">
                        {shipIds.map((id) => (
                            <li key={id}>
                                <label className="cursor-pointer flex items-center gap-2 w-full">
                                    <input
                                        type="checkbox"
                                        value={id}
                                        className="checkbox checkbox-secondary"
                                        checked={selectedTsIds.includes(id)}
                                        onChange={handleTsIdChange}
                                    />
                                    <span className="label-text">{id}</span>
                                </label>
                            </li>
                        ))}
                    </ul>
                </div>
        
                <input
                    type="number" 
                    className="input input-bordered input-secondary w-full"
                    placeholder="Time Length (unit: 10 min)"
                    value={timeLength}
                    onChange={handleTimeLengthChange}
                />

                <button className="btn btn-primary mt-4" onClick={handleCheckShipDomain}>Check Ship Domain of OS</button>

                <button className="btn btn-accent mt-4" onClick={handleCollisionRisk}>Calculate Collision Risk with TS</button>

                <div className="form-control w-full mt-4">
                    <label className="label cursor-pointer">
                        <span className="label-text">
                            {/* Toggle Map Layer: {currentTileLayer.url === esriTileLayer.url ? 'Esri World Imagery' : 'OpenStreetMap'} */}
                            Toggle Map Layer: {currentTileLayer.url === usgsTileLayer.url ? 'USGS USImagery (U.S. Public Domain)' : 'OpenStreetMap Humanitarian (CC0)'}
                        </span>
                        <input 
                            type="checkbox" 
                            className="toggle toggle-success" 
                            onChange={toggleTileLayer} 
                            // checked={currentTileLayer.url === esriTileLayer.url}
                            checked={currentTileLayer.url === usgsTileLayer.url}
                        />
                    </label>
                </div>

            </div>
            
            <div className="w-3/4 h-[80vh] ml-4 z-10">
                <VesselMap
                    geojsonData={geojsonData}
                    tileLayerUrl={currentTileLayer.url}
                    tileLayerAttribution={currentTileLayer.attribution}
                />
            </div>

            <div className="absolute top-25 right-0 p-4 z-20">
                <div className="stats stats-vertical shadow w-auto max-w-xs break-words">
                    <div className="stat place-items-center">
                        <div className="stat-title">VO</div>
                        <div className="stat-value">{calculationResult[0]}</div>
                        <div className="stat-desc">velocity obstacles region (TS)
                            <span className="text-secondary font-bold"> (km<sup>2</sup>)</span>
                        </div>
                    </div>

                    <div className="stat place-items-center">
                        <div className="stat-title">VR</div>
                        <div className="stat-value">{calculationResult[1]}</div>
                        <div className="stat-desc">velocity region (OS)
                            <span className="text-secondary font-bold"> (km<sup>2</sup>)</span>
                        </div>
                    </div>

                    <div className="stat place-items-center">
                        <div className="stat-title font-bold">VO-CRI</div>
                        <div className="stat-value text-accent">{calculationResult[2]}</div>
                        <div className="stat-desc text-secondary font-bold">collision risk index</div>
                    </div>

                    <div className="stat place-items-center">
                        <div className="stat-title">TCR</div>
                        <div className="stat-value">{Math.round((calculationResult[3] * 100) * 100000) / 100000}</div>
                        <div className="stat-desc">time-varying collision risk
                            <span className="text-secondary font-bold"> (%)</span>
                        </div>
                    </div>

                    <div className="stat place-items-center">
                        <div className="stat-title">TCPA</div>
                        <div className="stat-value">{calculationResult[4]}</div>
                        <div className="stat-desc">time to closest point of approach
                            <span className="text-secondary font-bold"> (min)</span>
                        </div>
                    </div>
                </div>
            </div>

            {calculationResult[2] >= 0.5 && (
                <div className="absolute bottom-[18vh] left-1/4 w-2/3 z-30">
                    <div role="alert" className="alert alert-warning">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-6 w-6 shrink-0 stroke-current"
                            fill="none"
                            viewBox="0 0 24 24">
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <span>Warning: High Collision Risk Index [Action of collision avoidance required]</span>
                    </div>
                </div>
            )}

            {(0.25 <= calculationResult[2]) && (calculationResult[2] < 0.5) && (
                <div className="absolute bottom-[18vh] left-1/4 w-2/3 z-30">
                    <div role="alert" className="alert alert-warning">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-6 w-6 shrink-0 stroke-current"
                            fill="none"
                            viewBox="0 0 24 24">
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <span>Warning: Moderate Collision Risk Index</span>
                    </div>
                </div>
            )}

            {(0 < calculationResult[2]) && (calculationResult[2] < 0.25) && (
                <div className="absolute bottom-[18vh] left-1/4 w-2/3 z-30">
                    <div role="alert" className="alert alert-info">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-6 w-6 shrink-0 stroke-current"
                            fill="none"
                            viewBox="0 0 24 24">
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>Low Collision Risk Index</span>
                    </div>
                </div>
            )}

            {isResultUpdated && (calculationResult[2] <= 0) && (
                <div className="absolute bottom-[18vh] left-1/4 w-2/3 z-30">
                    <div role="alert" className="alert alert-success">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-6 w-6 shrink-0 stroke-current"
                            fill="none"
                            viewBox="0 0 24 24">
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>Current OS is Safe with Selected TS</span>
                    </div>
                </div>
            )}

        </div>
  )
}

export default TestComp