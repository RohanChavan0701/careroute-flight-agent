## Flight API (v1)

Authentication: send header `x-api-key: $API_KEY`.

Base URL: http://localhost:8000

### Start tracking

POST `/v1/flights/track`

Body:

```json
{
  "airline_code": "AA",
  "flight_number": "100",
  "departure_date": "2025-10-11"
}
```

Example:

```bash
http POST :8000/v1/flights/track x-api-key:$API_KEY airline_code=AA flight_number=100 departure_date=2025-10-11
```

### Get current status

GET `/v1/flights/{id}`

Example:

```bash
http GET :8000/v1/flights/AA-100-2025-10-11 x-api-key:$API_KEY
```

### Get events

GET `/v1/flights/{id}/events`

```bash
http GET :8000/v1/flights/AA-100-2025-10-11/events x-api-key:$API_KEY
```

### Stop tracking

DELETE `/v1/flights/{id}`

```bash
http DELETE :8000/v1/flights/AA-100-2025-10-11 x-api-key:$API_KEY
```

### LLM tool: get_flight_status

POST `/v1/tools/get_flight_status`

Form/query param: `flight_id`

```bash
http POST :8000/v1/tools/get_flight_status flight_id=AA-100-2025-10-11 x-api-key:$API_KEY
```


