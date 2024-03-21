stream_schema = [{
    "name": "job_openings",
    "supported_sync_modes": [
        "full_refresh",
        "incremental"
    ],
    "source_defined_cursor": False,
    "json_schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "job_type": {
                "type": "string"
            },
            "job_title": {
                "type": "string"
            },
            "job_role": {
                "type": "string"
            },
            "job_description_url": {
                "type": "string"
            },
            "job_description_url_without_job_id": {
                "type": "string",
                "uniqueItems": True
            },
            "job_description_raw_text": {
                "type": "string"
            },
            "min_experience": {
                "type": "string"
            },
            "max_experience": {
                "type": "string"
            },
            "min_ctc": {
                "type": "string"
            },
            "max_ctc": {
                "type": "string"
            },
            "job_location": {
                "type": "string"
            },
            "skills": {
                "type": "object"
            },
            "relevancy_score": {
                "type": "number"
            },
            "raw_response": {
                "type": "object"
            },
            "job_source": {
                "type": "string",
                "enum": ["naukri", "linkedin", "google_jobs", "hirist", "instahyre", "internshala"]
            },
            "is_duplicate": {
                "type": "boolean",
                "default": False
            },
            "company": {
                "type": "string"
            },
            "department": {
                "type": "string"
            }
        }
    }
},
    {
        "name": "job_roles",
        "supported_sync_modes": [
            "full_refresh",
            "incremental"
        ],
        "source_defined_cursor": False,
        "json_schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "uniqueItems": True
                }
            }
        }
    },
    {
        "name": "companies",
        "supported_sync_modes": [
            "full_refresh",
            "incremental"
        ],
        "source_defined_cursor": False,
        "json_schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "uniqueItems": True
                },
                "linkedin_url": {
                    "type": "string",
                    "uniqueItems": True
                }
            }
        }
    },
    {
        "name": "recruiter_details",
        "supported_sync_modes": [
            "full_refresh",
            "incremental"
        ],
        "source_defined_cursor": False,
        "json_schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "linkedin_profile_url": {
                    "type": "string",
                    "uniqueItems": True
                },
                "short_intro": {
                    "type": "string"
                },
                "company": {
                    "type": "string"
                },
                "contact_number": {
                    "type": "string"
                },
                "country_code": {
                    "type": "string"
                },
                "hiring_manager_for_job_link": {
                    "type": "string"
                }
            }
        }
    }
]
