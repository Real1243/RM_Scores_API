## Week 1 – RM Scores API Development

### Work Done
- Built a REST API for RM score retrieval
- Integrated PostgreSQL database connection using psycopg2
- Implemented endpoint to fetch RM scores based on region and superadmin
- Tested the API using Postman

### Problems Faced
- Initial database connection errors due to incorrect `.env` path
- Import errors due to incorrect project structure
- SQL query returned empty results due to mismatched filters

### Solution
- Fixed database connection configuration and ensured `.env` is loaded correctly
- Reorganized files so modules import correctly
- Verified data in pgAdmin and corrected query filters

### Outcome
- API successfully returns RM score data for given region
- Postman tests confirmed correct JSON response format and data

### Screenshots
![Postman API Response](docs\week01\screenshots\API_Response_Scores.png.png)
(docs\week01\screenshots\API_Response.png.png)
(docs\week01\screenshots\Postman_Response.png.png)
(docs\week01\screenshots\SQL_Query_Response.png)


### API Testing (Postman)
- Endpoint: `GET /rm-scores`
- Response:
  ```json
  {
    "region": "Mumbai",
    "average_score": 13.35,
    "best_score": 16,
    "worst_score": 3
  }

