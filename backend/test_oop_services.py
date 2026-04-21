import pytest
from unittest.mock import MagicMock
from oop_api import BaseService, DiseaseService, LocationService, CaseService

# 1. Test the Class Hierarchy -> Base structure is abstract
def test_baseservice_is_abstract():
    with pytest.raises(TypeError) as exc:
        BaseService(client=MagicMock())
    assert "Can't instantiate abstract class" in str(exc.value)

# Mock client setup
def mock_client_table(data_to_return=None):
    client = MagicMock()
    table_mock = MagicMock()
    query_mock = MagicMock()
    query_mock.execute.return_value = MagicMock(data=data_to_return or [])
    query_mock.select.return_value = query_mock
    query_mock.order.return_value = query_mock
    query_mock.eq.return_value = query_mock
    query_mock.insert.return_value = query_mock
    query_mock.update.return_value = query_mock
    query_mock.delete.return_value = query_mock
    query_mock.limit.return_value = query_mock
    table_mock.select.return_value = query_mock
    table_mock.insert.return_value = query_mock
    table_mock.update.return_value = query_mock
    table_mock.delete.return_value = query_mock
    client.table.return_value = table_mock
    return client

# 2. Test DiseaseService (Testing subclasses and overridden behavior)
def test_disease_service_hierarchy_and_base_methods():
    client = mock_client_table([{"disease_id": 1, "name": "Flu"}])
    service = DiseaseService(client)
    
    # Check hierarchy
    assert isinstance(service, BaseService)
    assert service.table_name == "diseases"

    # Check Base class method (from inheritance)
    data = service.get_all()
    assert len(data) == 1
    assert data[0]["name"] == "Flu"
    
    # Check Private validation method usage
    with pytest.raises(ValueError):
        service._validate_payload({"name": "Bad"}) # Missing category
        
    payload = service._validate_payload({"name": "Flu", "category": "Respiratory"})
    assert payload["category"] == "Respiratory"

def test_disease_service_overridden_create():
    client = mock_client_table([{"disease_id": 2, "name": "Cold"}])
    service = DiseaseService(client)
    
    # Different behavior: create calls _validate_payload
    # Which checks for category
    result = service.create({"name": "Cold", "category": "Respiratory"})
    assert len(result) == 1

# 3. Test LocationService 
def test_location_service_overrides_and_validation():
    client = mock_client_table([{"city": "Syracuse"}])
    service = LocationService(client)
    
    # Private method overrides
    with pytest.raises(ValueError) as exc:
        service._validate_payload({"country": "USA"}) # Missing city
    
    payload = service._validate_payload({"city": "Syracuse", "country": "USA"})
    assert payload["city"] == "Syracuse"

    # Base class functionality via subclass
    data = service.get_all()
    assert data[0]["city"] == "Syracuse"

# 4. Test CaseService 
def test_case_service_polymorphism():
    client = mock_client_table([{"case_id": 100, "case_count": 5}])
    service = CaseService(client)
    
    assert isinstance(service, BaseService)
    
    # Polymorphism: get_all selects specific base_select columns
    service.get_all()
    client.table().select.assert_called_with(service.base_select)
    
    # Private internal validation method testing
    with pytest.raises(ValueError):
        service._validate_payload({"date_reported": "2026-04-20"}) # Missing case_count
        
    payload = service._validate_payload({"case_count": 10, "date_reported": "2026-04-20"})
    assert payload["case_count"] == 10

    # Overridden standard method (CRUD works for CaseService specifically)
    result = service.create({"case_count": 10})
    assert result[0]["case_id"] == 100
