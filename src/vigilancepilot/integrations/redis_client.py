"""
Redis and RedisVL client for vector storage and similarity search.
"""

from typing import List, Dict, Any, Optional
import json
...existing code...

try:
    ...existing code...
    ...existing code...
    ...existing code...
    REDIS_SEARCH_AVAILABLE = True
except ImportError:
    REDIS_SEARCH_AVAILABLE = False


...existing code...
    """
    Client for Redis operations including vector similarity search via RedisVL.
    """
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 6379, 
        password: Optional[str] = None,
        db: int = 0,
        decode_responses: bool = True
    ):
        """
        Initialize Redis client.
        
        Args:
            host: Redis host
            port: Redis port
            password: Redis password (if required)
            db: Redis database number
            decode_responses: Whether to decode responses to strings
        """
        self.client = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=decode_responses
        )
        self._test_connection()
    
    def _test_connection(self):
        """Test Redis connection."""
        try:
            self.client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def store_validation_result(self, key: str, result: Dict[str, Any], ttl: Optional[int] = None):
        """
        Store a validation result in Redis.
        
        Args:
            key: Redis key
            result: Validation result data
            ttl: Time-to-live in seconds (optional)
        """
        self.client.set(key, json.dumps(result), ex=ttl)
    
    def get_validation_result(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a validation result from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            Validation result data or None
        """
        data = self.client.get(key)
        return json.loads(data) if data else None
    
    def store_collection_metadata(self, collection_id: str, metadata: Dict[str, Any]):
        """
        Store collection metadata.
        
        Args:
            collection_id: Collection ID
            metadata: Metadata dictionary
        """
        key = f"collection:{collection_id}:metadata"
        self.client.hset(key, mapping=metadata)
    
    def get_collection_metadata(self, collection_id: str) -> Dict[str, Any]:
        """
        Retrieve collection metadata.
        
        Args:
            collection_id: Collection ID
            
        Returns:
            Metadata dictionary
        """
        key = f"collection:{collection_id}:metadata"
        return self.client.hgetall(key)
    
    def create_vector_index(
        self, 
        index_name: str, 
        vector_dim: int = 1536,
        distance_metric: str = "COSINE"
    ):
        """
        Create a vector search index for similarity search.
        
        Args:
            index_name: Name of the index
            vector_dim: Dimension of the vectors
            distance_metric: Distance metric (COSINE, L2, IP)
        """
        try:
            # Check if index already exists
            self.client.ft(index_name).info()
            print(f"Index {index_name} already exists")
            return
        except redis.ResponseError:
            pass  # Index doesn't exist, create it
        
        # Define schema
        schema = (
            TextField("content"),
            TextField("metadata"),
            VectorField(
                "embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": vector_dim,
                    "DISTANCE_METRIC": distance_metric,
                }
            )
        )
        
        # Create index
        definition = IndexDefinition(prefix=[f"{index_name}:"], index_type=IndexType.HASH)
        self.client.ft(index_name).create_index(schema, definition=definition)
    
    def store_vector(
        self, 
        index_name: str, 
        doc_id: str, 
        content: str, 
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store a document with its vector embedding.
        
        Args:
            index_name: Name of the index
            doc_id: Document ID
            content: Text content
            embedding: Vector embedding
            metadata: Optional metadata
        """
        key = f"{index_name}:{doc_id}"
        
        # Convert embedding to bytes
        import numpy as np
        embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
        
        data = {
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "embedding": embedding_bytes
        }
        
        self.client.hset(key, mapping=data)
    
    def search_vectors(
        self, 
        index_name: str, 
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            index_name: Name of the index
            query_embedding: Query vector
            top_k: Number of results to return
            
        Returns:
            List of similar documents with scores
        """
        import numpy as np
        
        # Convert query embedding to bytes
        query_bytes = np.array(query_embedding, dtype=np.float32).tobytes()
        
        # Create query
        query = (
            Query(f"*=>[KNN {top_k} @embedding $vec AS score]")
            .return_fields("content", "metadata", "score")
            .sort_by("score")
            .dialect(2)
        )
        
        # Execute search
        results = self.client.ft(index_name).search(
            query, 
            query_params={"vec": query_bytes}
        )
        
        # Parse results
        docs = []
        for doc in results.docs:
            docs.append({
                "id": doc.id,
                "content": doc.content,
                "metadata": json.loads(doc.metadata),
                "score": float(doc.score)
            })
        
        return docs
    
    def cache_llm_response(self, prompt_hash: str, response: str, ttl: int = 3600):
        """
        Cache an LLM response.
        
        Args:
            prompt_hash: Hash of the prompt (for cache key)
            response: LLM response
            ttl: Time-to-live in seconds
        """
        key = f"llm_cache:{prompt_hash}"
        self.client.set(key, response, ex=ttl)
    
    def get_cached_llm_response(self, prompt_hash: str) -> Optional[str]:
        """
        Retrieve a cached LLM response.
        
        Args:
            prompt_hash: Hash of the prompt
            
        Returns:
            Cached response or None
        """
        key = f"llm_cache:{prompt_hash}"
        return self.client.get(key)
