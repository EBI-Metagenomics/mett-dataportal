"""
Basic PyHMMER functionality tests that don't require complex database setup.

These tests focus on schema validation, basic API structure, and core functionality
without requiring database connections or complex test data setup.
"""

from django.test import TestCase

from pyhmmer_search.search.schemas import SearchRequestSchema, HitSchema


class TestPyhmmerBasicFunctionality(TestCase):
    """Basic tests for PyHMMER functionality that don't require database setup."""

    def test_search_request_schema_validation(self):
        """Test that SearchRequestSchema validates correctly."""
        # Valid request
        valid_request = {
            "database": "bu_pv_all",
            "threshold": "evalue",
            "threshold_value": 0.01,
            "input": ">Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
            "E": 1.0,
            "domE": 1.0,
            "incE": 0.01,
            "incdomE": 0.03,
            "T": None,
            "domT": None,
            "incT": None,
            "incdomT": None,
            "popen": 0.02,
            "pextend": 0.4,
        }

        try:
            schema = SearchRequestSchema(**valid_request)
            self.assertEqual(schema.database, "bu_pv_all")
            self.assertEqual(schema.threshold, "evalue")
            self.assertEqual(schema.threshold_value, 0.01)
            self.assertEqual(
                schema.input,
                ">Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
            )
        except Exception as e:
            self.fail(f"Valid request should not raise exception: {e}")

    # def test_search_request_schema_invalid_data(self):
    #     """Test that SearchRequestSchema rejects invalid data."""
    #     # Invalid threshold value
    #     invalid_request = {
    #         "database": "bu_pv_all",
    #         "threshold": "evalue",
    #         "threshold_value": -1.0,  # Invalid negative value
    #         "input": ">Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
    #         "E": 1.0,
    #         "domE": 1.0,
    #         "incE": 0.01,
    #         "incdomE": 0.03
    #     }

    #     with self.assertRaises(Exception):
    #         SearchRequestSchema(**invalid_request)

    def test_hit_schema_creation(self):
        """Test that HitSchema can be created with valid data."""
        valid_hit_data = {
            "target": "BU_GENE_1",
            "description": "Test gene 1",
            "evalue": "1e-10",
            "score": "100.0",
            "num_hits": 3,
            "num_significant": 2,
            "is_significant": True,
            "domains": [],
        }

        try:
            hit = HitSchema(**valid_hit_data)
            self.assertEqual(hit.target, "BU_GENE_1")
            self.assertEqual(hit.description, "Test gene 1")
            self.assertEqual(hit.evalue, "1e-10")
            self.assertEqual(hit.score, "100.0")
            self.assertEqual(hit.num_hits, 3)
            self.assertEqual(hit.num_significant, 2)
            self.assertTrue(hit.is_significant)
            self.assertEqual(len(hit.domains), 0)
        except Exception as e:
            self.fail(f"Valid hit data should not raise exception: {e}")


#     def test_domain_schema_creation(self):
#         """Test that DomainSchema can be created with valid data."""
#         valid_domain_data = {
#             "env_from": 1,
#             "env_to": 50,
#             "bitscore": 100.0,
#             "ievalue": 1e-10,
#             "is_significant": True
#         }

#         try:
#             domain = DomainSchema(**valid_domain_data)
#             self.assertEqual(domain.env_from, 1)
#             self.assertEqual(domain.env_to, 50)
#             self.assertEqual(domain.bitscore, 100.0)
#             self.assertEqual(domain.ievalue, 1e-10)
#             self.assertTrue(domain.is_significant)
#         except Exception as e:
#             self.fail(f"Valid domain data should not raise exception: {e}")

#     def test_api_router_initialization(self):
#         """Test that the API router is properly initialized."""
#         # Check that the router has the expected endpoints
#         routes = pyhmmer_router_search.routes

#         # Should have at least the search endpoint
#         self.assertIsNotNone(routes)
#         self.assertGreater(len(routes), 0)

#     def test_api_response_structure(self):
#         """Test basic API response structure without database operations."""
#         client = TestClient(pyhmmer_router_search)

#         # Test with empty request (should fail validation)
#         response = client.post("", json={})

#         # Should return 422 (validation error) for empty request
#         self.assertEqual(response.status_code, 422)

#         # Response should contain error details
#         response_data = response.json()
#         self.assertIsInstance(response_data, dict)

#     def test_threshold_validation_logic(self):
#         """Test threshold validation logic."""
#         # Test E-value threshold validation
#         valid_evalue_request = {
#             "database": "bu_pv_all",
#             "threshold": "evalue",
#             "threshold_value": 0.01,
#             "input": ">Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
#             "E": 1.0,
#             "domE": 1.0,
#             "incE": 0.01,
#             "incdomE": 0.03
#         }

#         try:
#             schema = SearchRequestSchema(**valid_evalue_request)
#             # E-value threshold should be positive
#             self.assertGreater(schema.threshold_value, 0)
#             # incE should be <= E
#             self.assertLessEqual(schema.incE, schema.E)
#         except Exception as e:
#             self.fail(f"Valid E-value request should not raise exception: {e}")

#         # Test Bit Score threshold validation
#         valid_bitscore_request = {
#             "database": "bu_pv_all",
#             "threshold": "bitscore",
#             "threshold_value": 25.0,
#             "input": ">Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
#             "T": 20.0,
#             "domT": 20.0,
#             "incT": 25.0,
#             "incdomT": 25.0
#         }

#         try:
#             schema = SearchRequestSchema(**valid_bitscore_request)
#             # Bit score threshold should be positive
#             self.assertGreater(schema.threshold_value, 0)
#             # incT should be >= T
#             self.assertGreaterEqual(schema.incT, schema.T)
#         except Exception as e:
#             self.fail(f"Valid bit score request should not raise exception: {e}")

#     def test_sequence_validation(self):
#         """Test sequence input validation."""
#         # Test with valid sequence
#         valid_sequence = ">Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY"
#         valid_request = {
#             "database": "bu_pv_all",
#             "threshold": "evalue",
#             "threshold_value": 0.01,
#             "input": valid_sequence,
#             "E": 1.0,
#             "domE": 1.0,
#             "incE": 0.01,
#             "incdomE": 0.03
#         }

#         try:
#             schema = SearchRequestSchema(**valid_request)
#             self.assertEqual(schema.input, valid_sequence)
#             self.assertGreater(len(schema.input), 0)
#         except Exception as e:
#             self.fail(f"Valid sequence should not raise exception: {e}")

#         # Test with empty sequence (should fail validation)
#         invalid_request = {
#             "database": "bu_pv_all",
#             "threshold": "evalue",
#             "threshold_value": 0.01,
#             "input": "",  # Empty sequence
#             "E": 1.0,
#             "domE": 1.0,
#             "incE": 0.01,
#             "incdomE": 0.03
#         }

#         with self.assertRaises(Exception):
#             SearchRequestSchema(**invalid_request)


# class TestPyhmmerSchemaCompatibility(TestCase):
#     """Tests for schema compatibility and data types."""

#     def test_numeric_field_types(self):
#         """Test that numeric fields accept appropriate types."""
#         # Test with float values
#         float_request = {
#             "database": "bu_pv_all",
#             "threshold": "evalue",
#             "threshold_value": 0.01,
#             "input": ">Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
#             "E": 1.0,
#             "domE": 0.5,
#             "incE": 0.01,
#             "incdomE": 0.03,
#             "popen": 0.02,
#             "pextend": 0.4
#         }

#         try:
#             schema = SearchRequestSchema(**float_request)
#             self.assertIsInstance(schema.E, float)
#             self.assertIsInstance(schema.domE, float)
#             self.assertIsInstance(schema.incE, float)
#             self.assertIsInstance(schema.incdomE, float)
#         except Exception as e:
#             self.fail(f"Float values should be accepted: {e}")

#     def test_optional_field_handling(self):
#         """Test that optional fields are handled correctly."""
#         # Test with minimal required fields
#         minimal_request = {
#             "database": "bu_pv_all",
#             "threshold": "evalue",
#             "threshold_value": 0.01,
#             "input": ">Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY"
#         }

#         try:
#             schema = SearchRequestSchema(**minimal_request)
#             # Optional fields should have default values or be None
#             self.assertIsNotNone(schema.database)
#             self.assertIsNotNone(schema.threshold)
#             self.assertIsNotNone(schema.threshold_value)
#             self.assertIsNotNone(schema.input)
#         except Exception as e:
#             self.fail(f"Minimal request should be valid: {e}")

#     def test_string_field_validation(self):
#         """Test string field validation."""
#         # Test with valid string values
#         valid_string_request = {
#             "database": "bu_pv_all",
#             "threshold": "evalue",
#             "threshold_value": 0.01,
#             "input": ">Example protein sequence\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
#             "E": 1.0,
#             "domE": 1.0,
#             "incE": 0.01,
#             "incdomE": 0.03
#         }

#         try:
#             schema = SearchRequestSchema(**valid_string_request)
#             self.assertIsInstance(schema.database, str)
#             self.assertIsInstance(schema.threshold, str)
#             self.assertIsInstance(schema.input, str)
#         except Exception as e:
#             self.fail(f"String values should be accepted: {e}")
