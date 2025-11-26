"""
Type Batch Generator

This module implements the TypeBatchGenerator class for generating
multiple variations of assets based on ElementType definitions.

Features:
- Batch generation from type definitions
- Integration with existing batch API
- Support for multiple variation strategies
- Parameter overrides and customization
- Progress tracking and error handling
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
from datetime import datetime

# Import generator components
from .base_generator import BaseGenerator
from .dynamic_loader import DynamicGeneratorLoader
from .variation_strategies import VariationEngine

# Import type system components
try:
    from enhanced_design.element_types import ElementType, DiversityConfig
    HAS_TYPE_SYSTEM = True
except ImportError:
    HAS_TYPE_SYSTEM = False
    # Create mock classes for fallback
    ElementType = None
    DiversityConfig = None

# Import batch system components
try:
    from utils.batch_job import BatchJob, BatchJobStatus
    HAS_BATCH_SYSTEM = True
except ImportError:
    HAS_BATCH_SYSTEM = False
    # Create mock classes for fallback
    class BatchJob:
        def __init__(self, *args, **kwargs):
            self.id = str(uuid.uuid4())
            self.status = "pending"
    class BatchJobStatus:
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"


class TypeBatchGenerator:
    """
    Batch generator for creating multiple variations from ElementType definitions.
    
    This class provides:
    - Batch processing of ElementTypes
    - Integration with existing batch API
    - Support for all variation strategies
    - Progress tracking and error handling
    - Parameter customization and overrides
    """
    
    def __init__(self, 
                 dynamic_loader: Optional[DynamicGeneratorLoader] = None,
                 max_workers: int = 4,
                 variation_engine: Optional[VariationEngine] = None):
        """
        Initialize the type batch generator.
        
        Args:
            dynamic_loader: DynamicGeneratorLoader instance
            max_workers: Maximum number of worker threads
            variation_engine: VariationEngine for diversity strategies
        """
        self.dynamic_loader = dynamic_loader or DynamicGeneratorLoader()
        self.variation_engine = variation_engine or VariationEngine()
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
        
        # Batch tracking
        self.active_batches: Dict[str, BatchJob] = {}
        self.completed_batches: Dict[str, BatchJob] = {}
        
        self.logger.info(f"Initialized TypeBatchGenerator with {max_workers} workers")
    
    def generate_batch_from_types(self,
                                type_ids: List[str],
                                count_per_type: int = 5,
                                parameter_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
                                diversity_configs: Optional[Dict[str, DiversityConfig]] = None,
                                seeds: Optional[Dict[str, int]] = None,
                                output_format: str = 'image',
                                custom_metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a batch of assets from multiple ElementTypes.
        
        Args:
            type_ids: List of ElementType IDs to generate from
            count_per_type: Number of variations to generate per type
            parameter_overrides: Optional parameter overrides per type
            diversity_configs: Optional diversity configs per type
            seeds: Optional seeds per type for reproducible results
            output_format: Output format ('image', 'metadata', 'both')
            custom_metadata: Optional custom metadata to include
            
        Returns:
            Batch job ID for tracking progress
            
        Raises:
            ValueError: If type system is not available or invalid parameters
            RuntimeError: If batch creation fails
        """
        if not HAS_TYPE_SYSTEM:
            raise RuntimeError("Type system not available - cannot generate batch from types")
        
        # Validate inputs
        if not type_ids:
            raise ValueError("type_ids cannot be empty")
        
        if count_per_type <= 0:
            raise ValueError("count_per_type must be positive")
        
        # Create batch job
        batch_id = str(uuid.uuid4())
        batch_job = BatchJob(
            id=batch_id,
            status=BatchJobStatus.PENDING,
            created_at=datetime.now(),
            metadata={
                'type_ids': type_ids,
                'count_per_type': count_per_type,
                'output_format': output_format,
                'custom_metadata': custom_metadata or {},
                'total_items': len(type_ids) * count_per_type
            }
        )
        
        # Store batch job
        self.active_batches[batch_id] = batch_job
        
        try:
            # Start batch processing in background
            self._process_batch_async(batch_job, parameter_overrides, diversity_configs, seeds)
            
            self.logger.info(f"Created batch job {batch_id} for {len(type_ids)} types with {count_per_type} variations each")
            return batch_id
            
        except Exception as e:
            # Clean up failed batch
            if batch_id in self.active_batches:
                del self.active_batches[batch_id]
            self.logger.error(f"Failed to create batch job: {e}")
            raise RuntimeError(f"Failed to create batch job: {e}")
    
    def _process_batch_async(self,
                           batch_job: BatchJob,
                           parameter_overrides: Optional[Dict[str, Dict[str, Any]]],
                           diversity_configs: Optional[Dict[str, DiversityConfig]],
                           seeds: Optional[Dict[str, int]]):
        """
        Process a batch job asynchronously.
        
        Args:
            batch_job: BatchJob to process
            parameter_overrides: Parameter overrides per type
            diversity_configs: Diversity configs per type
            seeds: Seeds per type
        """
        import threading
        
        def process():
            try:
                batch_job.status = BatchJobStatus.RUNNING
                results = self._generate_batch_results(
                    batch_job, parameter_overrides, diversity_configs, seeds
                )
                
                # Store results
                batch_job.results = results
                batch_job.status = BatchJobStatus.COMPLETED
                batch_job.completed_at = datetime.now()
                
                # Move to completed batches
                self.completed_batches[batch_job.id] = batch_job
                if batch_job.id in self.active_batches:
                    del self.active_batches[batch_job.id]
                
                self.logger.info(f"Completed batch job {batch_job.id} with {len(results)} results")
                
            except Exception as e:
                # Mark batch as failed
                batch_job.status = BatchJobStatus.FAILED
                batch_job.error = str(e)
                batch_job.completed_at = datetime.now()
                
                self.logger.error(f"Batch job {batch_job.id} failed: {e}")
        
        # Start processing in background thread
        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()
    
    def _generate_batch_results(self,
                              batch_job: BatchJob,
                              parameter_overrides: Optional[Dict[str, Dict[str, Any]]],
                              diversity_configs: Optional[Dict[str, DiversityConfig]],
                              seeds: Optional[Dict[str, int]]) -> List[Dict[str, Any]]:
        """
        Generate results for a batch job.
        
        Args:
            batch_job: BatchJob to generate results for
            parameter_overrides: Parameter overrides per type
            diversity_configs: Diversity configs per type
            seeds: Seeds per type
            
        Returns:
            List of generation results
        """
        type_ids = batch_job.metadata['type_ids']
        count_per_type = batch_job.metadata['count_per_type']
        output_format = batch_job.metadata['output_format']
        custom_metadata = batch_job.metadata['custom_metadata']
        
        results = []
        generated_count = 0
        
        # Process each type
        for type_id in type_ids:
            # Get overrides for this type
            type_overrides = parameter_overrides.get(type_id, {}) if parameter_overrides else {}
            type_diversity = diversity_configs.get(type_id) if diversity_configs else None
            type_seed = seeds.get(type_id) if seeds else None
            
            # Generate variations for this type
            type_results = self._generate_type_variations(
                type_id=type_id,
                count=count_per_type,
                parameter_overrides=type_overrides,
                diversity_config=type_diversity,
                seed=type_seed,
                output_format=output_format,
                custom_metadata=custom_metadata
            )
            
            results.extend(type_results)
            generated_count += len(type_results)
            
            # Update batch progress
            batch_job.progress = generated_count / batch_job.metadata['total_items']
        
        return results
    
    def _generate_type_variations(self,
                                type_id: str,
                                count: int,
                                parameter_overrides: Optional[Dict[str, Any]],
                                diversity_config: Optional[DiversityConfig],
                                seed: Optional[int],
                                output_format: str,
                                custom_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate multiple variations for a single ElementType.
        
        Args:
            type_id: ElementType ID
            count: Number of variations to generate
            parameter_overrides: Parameter overrides
            diversity_config: Diversity configuration
            seed: Base seed for reproducible results
            output_format: Output format
            custom_metadata: Custom metadata
            
        Returns:
            List of generation results for this type
        """
        results = []
        
        for i in range(count):
            try:
                # Generate unique seed for this variation
                variation_seed = seed + i if seed is not None else None
                
                # Create generator from type
                generator = self.dynamic_loader.create_generator_from_type_id(
                    type_id=type_id,
                    parameter_overrides=parameter_overrides,
                    diversity_config=diversity_config,
                    seed=variation_seed
                )
                
                if generator is None:
                    self.logger.warning(f"Could not create generator for type {type_id}")
                    continue
                
                # Generate the asset
                asset = generator.generate()
                
                # Prepare result data
                result = {
                    'batch_id': None,  # Will be set by caller
                    'type_id': type_id,
                    'variation_index': i,
                    'seed': variation_seed,
                    'parameters': parameter_overrides,
                    'generator_type': generator.get_generator_type(),
                    'generated_at': datetime.now(),
                    'custom_metadata': custom_metadata.copy()
                }
                
                # Add output based on format
                if output_format in ['image', 'both']:
                    result['image'] = asset
                
                if output_format in ['metadata', 'both']:
                    # Get generator metadata
                    result['metadata'] = {
                        'width': asset.width,
                        'height': asset.height,
                        'mode': asset.mode,
                        'generator_info': generator.get_generator_type()
                    }
                
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to generate variation {i} for type {type_id}: {e}")
                # Add error result
                results.append({
                    'type_id': type_id,
                    'variation_index': i,
                    'seed': seed + i if seed is not None else None,
                    'error': str(e),
                    'generated_at': datetime.now()
                })
        
        return results
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a batch job.
        
        Args:
            batch_id: Batch job ID
            
        Returns:
            Dictionary with batch status information or None
        """
        # Check active batches
        if batch_id in self.active_batches:
            batch = self.active_batches[batch_id]
            return {
                'id': batch_id,
                'status': batch.status,
                'progress': getattr(batch, 'progress', 0.0),
                'created_at': batch.created_at.isoformat() if hasattr(batch, 'created_at') else None,
                'completed_at': batch.completed_at.isoformat() if hasattr(batch, 'completed_at') else None,
                'metadata': batch.metadata
            }
        
        # Check completed batches
        if batch_id in self.completed_batches:
            batch = self.completed_batches[batch_id]
            return {
                'id': batch_id,
                'status': batch.status,
                'progress': 1.0,
                'created_at': batch.created_at.isoformat() if hasattr(batch, 'created_at') else None,
                'completed_at': batch.completed_at.isoformat() if hasattr(batch, 'completed_at') else None,
                'metadata': batch.metadata,
                'results_count': len(getattr(batch, 'results', [])),
                'total_items': batch.metadata.get('total_items', 0)
            }
        
        return None
    
    def get_batch_results(self, batch_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get results for a completed batch job.
        
        Args:
            batch_id: Batch job ID
            
        Returns:
            List of generation results or None
        """
        if batch_id in self.completed_batches:
            batch = self.completed_batches[batch_id]
            if hasattr(batch, 'results'):
                return batch.results
        
        return None
    
    def generate_quick_batch(self,
                           type_id: str,
                           count: int = 5,
                           seed: Optional[int] = None) -> List[Image.Image]:
        """
        Generate a quick batch of variations (synchronous, simple interface).
        
        Args:
            type_id: ElementType ID to generate from
            count: Number of variations to generate
            seed: Optional seed for reproducible results
            
        Returns:
            List of generated PIL Images
        """
        try:
            results = []
            
            for i in range(count):
                # Create generator from type
                variation_seed = seed + i if seed is not None else None
                generator = self.dynamic_loader.create_generator_from_type_id(
                    type_id=type_id,
                    seed=variation_seed
                )
                
                if generator:
                    # Generate the asset
                    asset = generator.generate()
                    results.append(asset)
                
            self.logger.info(f"Generated {len(results)} variations for type {type_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to generate quick batch for {type_id}: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the batch generator.
        
        Returns:
            Dictionary with batch generator statistics
        """
        return {
            'active_batches': len(self.active_batches),
            'completed_batches': len(self.completed_batches),
            'max_workers': self.max_workers,
            'dynamic_loader_stats': self.dynamic_loader.get_statistics(),
            'variation_strategies': self.variation_engine.get_available_strategies(),
            'type_system_available': HAS_TYPE_SYSTEM,
            'batch_system_available': HAS_BATCH_SYSTEM
        }
    
    def cleanup_old_batches(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed batch jobs.
        
        Args:
            max_age_hours: Maximum age in hours for completed batches
            
        Returns:
            Number of batches cleaned up
        """
        if not HAS_BATCH_SYSTEM:
            return 0
            
        cutoff_time = datetime.now()
        cleaned_count = 0
        
        # Clean up old completed batches
        expired_ids = []
        for batch_id, batch in self.completed_batches.items():
            if hasattr(batch, 'completed_at'):
                age_hours = (cutoff_time - batch.completed_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    expired_ids.append(batch_id)
        
        for batch_id in expired_ids:
            del self.completed_batches[batch_id]
            cleaned_count += 1
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old completed batches")
        
        return cleaned_count
    
    def __repr__(self) -> str:
        """String representation of the type batch generator."""
        return (f"TypeBatchGenerator("
                f"active_batches={len(self.active_batches)}, "
                f"completed_batches={len(self.completed_batches)}, "
                f"workers={self.max_workers})")