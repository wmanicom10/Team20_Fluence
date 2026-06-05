# OOP Service Refactor Worklog

Date: 2026-04-21

Summary:
- Added an abstract `BaseService` in `backend/services/base_service.py`.
- Added `DiseaseService`, `LocationService`, and `CaseService` in separate files under `backend/services/`.
- Moved disease, location, and case validation/query behavior into those concrete service classes.
- Updated the active backend API flow so `backend/oop_api.py` now uses the new service classes for CRUD-style backend operations.
- Kept the existing backend endpoints working after the refactor.

Reference commit link:
- Refactor commit: https://github.com/wmanicom10/Team20_Fluence/commit/deb2165

Notes:
- `CaseService.create()` performs case-specific validation including integer parsing, `YYYY-MM-DD` date validation, and non-negative case count checks.
- `DiseaseService.create()` performs disease-specific validation for `name`, `category`, and `severity_level`.
- `LocationService.create()` performs location-specific validation for required `country` and `city` fields.
