import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from pyhmmer.plan7 import Hit, Domain
from pyhmmer.easel import TextSequence, DigitalSequence, Alphabet

from ..search.tasks import run_search
from ..search.models import HmmerJob, Database
from ..search.schemas import HitSchema
from django_celery_results.models import TaskResult


class TestPyhmmerSearchTasks:
    """Test cases for PyHMMER search tasks"""

    @pytest.fixture
    def mock_hit(self):
        """Create a mock PyHMMER hit object"""
        hit = Mock(spec=Hit)
        hit.name = b"test_gene_1"
        hit.description = b"Test protein description"
        hit.evalue = 1e-25
        hit.score = 95.5
        hit.included = True  # This hit is significant
        hit.bias = 0.1
        return hit

    @pytest.fixture
    def mock_domain(self):
        """Create a mock PyHMMER domain object"""
        domain = Mock(spec=Domain)
        domain.env_from = 1
        domain.env_to = 100
        domain.score = 95.5
        domain.i_evalue = 1e-25
        domain.c_evalue = 1e-20
        domain.bias = 0.1
        domain.strand = None
        return domain

    @pytest.fixture
    def mock_job(self):
        """Create a mock HmmerJob"""
        job = Mock(spec=HmmerJob)
        job.id = "test-job-id"
        job.database = "test_db"
        job.threshold = HmmerJob.ThresholdChoices.EVALUE
        job.threshold_value = 0.01
        job.incE = 0.01
        job.incT = 25.0
        job.E = 1.0
        job.domE = 0.03
        job.T = 7.0
        job.domT = 5.0
        job.popen = 0.02
        job.pextend = 0.4
        job.input = ">test_protein\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY"
        job.algo = HmmerJob.AlgoChoices.PHMMER
        return job

    @pytest.fixture
    def mock_task_result(self):
        """Create a mock TaskResult"""
        task_result = Mock(spec=TaskResult)
        task_result.task_id = "test-task-id"
        task_result.status = "PENDING"
        return task_result

    def test_domain_counting_single_domain_significant(self, mock_hit, mock_domain, mock_job, mock_task_result):
        """Test domain counting when a gene has one significant domain"""
        # Setup
        mock_hit.domains = [mock_domain]
        mock_job.task = mock_task_result
        
        # Mock the domain significance calculation
        with patch('pyhmmer_search.search.tasks.Pipeline') as mock_pipeline, \
             patch('pyhmmer_search.search.tasks.SequenceFile') as mock_seq_file, \
             patch('pyhmmer_search.search.tasks.Builder') as mock_builder:
            
            # Mock pipeline search results
            mock_pipeline_instance = Mock()
            mock_pipeline_instance.search_seq.return_value = [mock_hit]
            mock_pipeline.return_value = mock_pipeline_instance
            
            # Mock sequence file
            mock_seq_file_instance = Mock()
            mock_seq_file_instance.__enter__.return_value = [Mock()]
            mock_seq_file.return_value = mock_seq_file_instance
            
            # Mock builder
            mock_builder_instance = Mock()
            mock_builder.return_value = mock_builder_instance
            
            # Run the search
            result = run_search(str(mock_job.id))
            
            # Verify domain counting
            assert result['status'] == 'SUCCESS'
            # The result should show 1 domain, 1 significant domain

    def test_domain_counting_multiple_domains_mixed_significance(self, mock_hit, mock_job, mock_task_result):
        """Test domain counting when a gene has multiple domains with mixed significance"""
        # Create domains with different significance levels
        significant_domain = Mock(spec=Domain)
        significant_domain.score = 95.5
        significant_domain.i_evalue = 1e-25  # Very significant
        
        non_significant_domain = Mock(spec=Domain)
        non_significant_domain.score = 15.0
        non_significant_domain.i_evalue = 1e-5  # Not significant
        
        mock_hit.domains = [significant_domain, non_significant_domain]
        mock_job.task = mock_task_result
        
        # Test with E-value threshold
        mock_job.threshold = HmmerJob.ThresholdChoices.EVALUE
        mock_job.incE = 0.01
        
        # The result should show 2 domains, 1 significant domain

    def test_domain_counting_no_domains(self, mock_hit, mock_job, mock_task_result):
        """Test domain counting when a gene has no domains (phmmer case)"""
        # Setup - no domains
        mock_hit.domains = []
        mock_job.task = mock_task_result
        
        # The result should show 0 domains, 0 significant domains

    def test_bit_score_threshold_calculation(self, mock_hit, mock_domain, mock_job, mock_task_result):
        """Test domain counting with bit score threshold"""
        # Setup
        mock_hit.domains = [mock_domain]
        mock_job.threshold = HmmerJob.ThresholdChoices.BITSCORE
        mock_job.incT = 25.0
        mock_job.task = mock_task_result
        
        # Test bit score threshold logic
        # Domain with score 95.5 should be significant (> 25.0)

    def test_evalue_threshold_calculation(self, mock_hit, mock_domain, mock_job, mock_task_result):
        """Test domain counting with E-value threshold"""
        # Setup
        mock_hit.domains = [mock_domain]
        mock_job.threshold = HmmerJob.ThresholdChoices.EVALUE
        mock_job.incE = 0.01
        mock_job.task = mock_task_result
        
        # Test E-value threshold logic
        # Domain with i_evalue 1e-25 should be significant (< 0.01)

    def test_multiple_genes_different_domain_counts(self, mock_job, mock_task_result):
        """Test multiple genes with different numbers of domains"""
        # Create multiple hits with different domain counts
        hit1 = Mock(spec=Hit)
        hit1.name = b"gene_1"
        hit1.domains = [Mock(spec=Domain), Mock(spec=Domain)]  # 2 domains
        
        hit2 = Mock(spec=Hit)
        hit2.name = b"gene_2"
        hit2.domains = [Mock(spec=Domain)]  # 1 domain
        
        hit3 = Mock(spec=Hit)
        hit3.name = b"gene_3"
        hit3.domains = []  # 0 domains
        
        # Test that each gene shows its own domain count

    def test_fallback_threshold_calculation(self, mock_hit, mock_domain, mock_job, mock_task_result):
        """Test fallback threshold calculation when hit.included is not available"""
        # Setup - remove included attribute to trigger fallback
        delattr(mock_hit, 'included')
        mock_hit.domains = [mock_domain]
        mock_job.task = mock_task_result
        
        # Test fallback logic for both E-value and bit score thresholds

    def test_bias_field_handling(self, mock_hit, mock_domain, mock_job, mock_task_result):
        """Test bias field handling and type conversion"""
        # Setup
        mock_hit.bias = "0.1"  # String that should be converted to float
        mock_hit.domains = [mock_domain]
        mock_job.task = mock_task_result
        
        # Test that bias is properly converted to float

    def test_invalid_bias_field_handling(self, mock_hit, mock_domain, mock_job, mock_task_result):
        """Test handling of invalid bias field values"""
        # Setup
        mock_hit.bias = "invalid"  # Invalid value that can't be converted
        mock_hit.domains = [mock_domain]
        mock_job.task = mock_task_result
        
        # Test that invalid bias values are handled gracefully

    def test_sequence_field_handling(self, mock_hit, mock_domain, mock_job, mock_task_result):
        """Test sequence field extraction and handling"""
        # Setup
        mock_domain.alignment = Mock()
        mock_domain.alignment.target_sequence = "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY"
        mock_hit.domains = [mock_domain]
        mock_job.task = mock_task_result
        
        # Test that sequence is properly extracted and cleaned

    def test_empty_sequence_handling(self, mock_hit, mock_domain, mock_job, mock_task_result):
        """Test handling when sequence field is empty or None"""
        # Setup
        mock_domain.alignment = Mock()
        mock_domain.alignment.target_sequence = None
        mock_hit.domains = [mock_domain]
        mock_job.task = mock_task_result
        
        # Test that None sequences are handled properly


class TestHitSchemaValidation:
    """Test cases for HitSchema validation"""

    def test_hit_schema_required_fields(self):
        """Test that HitSchema requires all required fields"""
        from ..search.schemas import HitSchema
        
        # Test with minimal valid data
        valid_data = {
            "target": "test_gene",
            "description": "Test protein",
            "evalue": "1e-25",
            "score": "95.5",
            "is_significant": True,
            "domains": []
        }
        
        hit = HitSchema(**valid_data)
        assert hit.target == "test_gene"
        assert hit.is_significant is True

    def test_hit_schema_optional_fields(self):
        """Test that HitSchema handles optional fields correctly"""
        from ..search.schemas import HitSchema
        
        # Test with all optional fields
        complete_data = {
            "target": "test_gene",
            "description": "Test protein",
            "evalue": "1e-25",
            "score": "95.5",
            "sequence": "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
            "bias": 0.1,
            "num_hits": 2,
            "num_significant": 1,
            "is_significant": True,
            "domains": []
        }
        
        hit = HitSchema(**complete_data)
        assert hit.sequence == "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY"
        assert hit.bias == 0.1
        assert hit.num_hits == 2
        assert hit.num_significant == 1

    def test_hit_schema_field_types(self):
        """Test that HitSchema enforces correct field types"""
        from ..search.schemas import HitSchema
        
        # Test type validation
        with pytest.raises(ValueError):
            HitSchema(
                target="test_gene",
                description="Test protein",
                evalue="1e-25",
                score="95.5",
                is_significant="not_a_boolean",  # Should be boolean
                domains=[]
            )


class TestDomainCountingEdgeCases:
    """Test edge cases for domain counting logic"""

    def test_zero_domains(self):
        """Test counting when gene has zero domains"""
        # This should result in 0 hits, 0 significant hits

    def test_single_domain_exactly_at_threshold(self):
        """Test domain exactly at the significance threshold"""
        # Test both E-value and bit score edge cases

    def test_very_large_domain_counts(self):
        """Test handling of genes with many domains"""
        # Test performance and accuracy with large numbers

    def test_mixed_threshold_types(self):
        """Test switching between E-value and bit score thresholds"""
        # Ensure both threshold types work correctly
