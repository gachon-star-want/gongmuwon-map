import json
from pathlib import Path
from uuid import UUID

def test_agency_coordinates_exist_and_are_valid():
    json_path = Path("/Users/lee_wonyoung/developer/public_officer_map/services/pipeline/src/public_officer_pipeline/entity/agency_coordinates.json")
    
    # 1. Verify file exists
    assert json_path.exists(), f"Coordinates file {json_path} does not exist"
    
    # 2. Load file and parse JSON
    with open(json_path, "r", encoding="utf-8") as f:
        coordinates = json.load(f)
        
    # 3. Verify it's a dictionary
    assert isinstance(coordinates, dict), "Coordinates should be a dictionary"
    
    # 4. Verify we successfully geocoded at least 52 agencies
    num_agencies = len(coordinates)
    print(f"Total geocoded agencies found: {num_agencies}")
    assert num_agencies >= 52, f"Expected at least 52 agencies, but got {num_agencies}"
    
    # 5. Verify the format of every entry:
    # {"agency_uuid": {"latitude": lat, "longitude": lng, "name": name, "address": road_address}}
    for agency_id, data in coordinates.items():
        # Verify key is a valid UUID
        try:
            UUID(agency_id)
        except ValueError:
            assert False, f"Agency ID '{agency_id}' is not a valid UUID"
            
        assert isinstance(data, dict), f"Data for {agency_id} should be a dictionary"
        
        # Verify keys
        assert "latitude" in data, f"latitude missing for {agency_id}"
        assert "longitude" in data, f"longitude missing for {agency_id}"
        assert "name" in data, f"name missing for {agency_id}"
        assert "address" in data, f"address missing for {agency_id}"
        
        lat = data["latitude"]
        lng = data["longitude"]
        name = data["name"]
        address = data["address"]
        
        # Verify types
        assert isinstance(lat, float), f"latitude should be a float, got {type(lat)} for {agency_id}"
        assert isinstance(lng, float), f"longitude should be a float, got {type(lng)} for {agency_id}"
        assert isinstance(name, str) and name.strip(), f"name should be a non-empty string, got '{name}' for {agency_id}"
        assert isinstance(address, str), f"address should be a string, got {type(address)} for {agency_id}"
        
        # Verify lat/lng ranges (Korea region)
        assert 33.0 <= lat <= 39.0, f"latitude {lat} out of Korea bounds for {agency_id}"
        assert 124.0 <= lng <= 132.0, f"longitude {lng} out of Korea bounds for {agency_id}"
        
    print("All checks passed successfully!")
