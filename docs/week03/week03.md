---

## **Week 3 – RM Topic-wise Best & Worst Score API (Backend Refactor + Frontend Integration)**

### **Objective**

Enhance the RM Scores API to compute **topic-wise best and worst scores per RM**, centralize HTTP status code handling inside the service layer, and integrate the API with a frontend interface for visualization and testing.

---

### **Work Done**

* Implemented topic-wise **best and worst score calculation** for each RM
* Parsed deeply nested `score_json` data (`summery_score → sections`)
* Refactored backend to:

  * Move all HTTP status codes (200, 300, 400, 401, 500) into the service function
  * Keep `main.py` strictly for routing and request handling
* Removed unnecessary exception variables to optimize memory usage
* Modified SQL query to fetch **all RMs across all regions** (no region-level filtering)
* Included `region` and `rm_id` in the API response
* Integrated backend API with frontend (`index.html`)
* Tested API behavior using Postman for different scenarios

---

### **Technical Decisions**

* **Separation of Concerns**

  * `main.py`: API routing only
  * `services/region_superadminid_scores.py`: business logic + status codes
* SQL restricted to:

  * Joins and data retrieval
* All score aggregation logic implemented in Python
* Used `RealDictCursor` for cleaner row access
* Defensive parsing for malformed or missing `score_json`

---

### **Status Codes Implemented**

| Status Code | Description           | Condition                                               |
| ----------- | --------------------- | ------------------------------------------------------- |
| **200**     | Success               | RM topic-wise scores computed successfully              |
| **300**     | Partial Data          | Some RM rows contained invalid or incomplete score data |
| **400**     | Bad Request           | Required parameters missing                             |
| **401**     | No Data               | No RM data available                                    |
| **500**     | Internal Server Error | Database connection or query failure                    |

---

### **Problems Faced**

* API initially returned scores only for a single region (Mumbai)
* `score_json` inconsistencies caused silent data drops
* Internal Server Error due to mismatch between SQL placeholders and parameters
* Confusion around testing status codes via browser vs Postman
* Redundant exception variables (`except Exception as e`) flagged during review

---

### **Solutions**

* Removed region-based filtering from SQL query
* Included `region` field directly in the SELECT clause
* Fixed SQL execution by removing unused parameters
* Added explicit validation and early returns for status codes
* Used Postman to simulate edge cases instead of browser testing
* Simplified exception handling to improve performance

---

### **Output**

* Topic-wise best and worst scores for **each RM**
* Region information included per RM
* Clean JSON response structure suitable for frontend rendering

Example Response:

```json
{
  "region": "All",
  "results": [
    {
      "rm_id": "RM102",
      "region": "Delhi",
      "topics": [
        {
          "topic": "Greeting",
          "best_score": 8,
          "worst_score": 5
        }
      ]
    }
  ]
}
```

---

### **API Testing (Postman)**

* Endpoint: `GET /rm-topic-scores`
* Tested scenarios:

  * Successful response (200)
  * Missing parameters (400)
  * No data available (401)
  * Partial data handling (300)
  * Database failure simulation (500)
* Postman tests used to validate correct status code behavior

---

### **Frontend Integration**

* Built basic frontend using HTML
* Connected frontend to backend API endpoint
* Displayed RM topic-wise scores dynamically
* Verified API accessibility via browser and Postman

---

### **Evidence**

* API tested successfully via Postman
* SQL queries verified in pgAdmin
* Backend logic validated via terminal execution
* Frontend output verified in browser

Screenshots available in:

```
docs/week03/screenshots/
```

---

### **Outcome**

* Fully functional, scalable RM analytics API
* Clean backend architecture aligned with best practices
* API supports organization-wide RM analysis
* Ready for further extensions (charts, filters, dashboards)

---


