"""
Sistema de Cache Avançado para Performance
Implementa cache em memória com TTL, invalidação inteligente e estatísticas
"""

import time
from typing import Any, Optional, Callable
from functools import wraps
import hashlib
import json


class AdvancedCache:
    """
    Sistema de cache avançado com:
    - TTL (Time To Live)
    - Invalidação por padrão
    - Estatísticas de hit/miss
    - LRU (Least Recently Used)
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Args:
            max_size: Número máximo de itens no cache
            default_ttl: TTL padrão em segundos
        """
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Estatísticas
        self.hits = 0
        self.misses = 0
        self.invalidations = 0
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Gera chave única baseada nos argumentos"""
        key_data = f"{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_expired(self, key: str) -> bool:
        """Verifica se item expirou"""
        if key not in self.cache:
            return True
        
        item = self.cache[key]
        if time.time() > item['expires_at']:
            del self.cache[key]
            del self.access_times[key]
            return True
        
        return False
    
    def _evict_lru(self):
        """Remove item menos recentemente usado"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times, key=self.access_times.get)
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def get(self, key: str) -> Optional[Any]:
        """Busca valor no cache"""
        if self._is_expired(key):
            self.misses += 1
            return None
        
        self.hits += 1
        self.access_times[key] = time.time()
        return self.cache[key]['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Armazena valor no cache"""
        # Se cache cheio, remove LRU
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        self.access_times[key] = time.time()
    
    def invalidate(self, pattern: str = None):
        """Invalida cache por padrão"""
        if pattern is None:
            # Limpa tudo
            self.cache.clear()
            self.access_times.clear()
            self.invalidations += len(self.cache)
        else:
            # Limpa por padrão
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
                del self.access_times[key]
            self.invalidations += len(keys_to_delete)
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do cache"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'invalidations': self.invalidations,
            'size': len(self.cache),
            'max_size': self.max_size
        }
    
    def clear(self):
        """Limpa todo o cache"""
        self.invalidate()


# Instância global
advanced_cache = AdvancedCache(max_size=1000, default_ttl=300)


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator para cachear resultados de funções
    
    Args:
        ttl: Tempo de vida em segundos
        key_prefix: Prefixo para a chave do cache
    
    Usage:
        @cached(ttl=60, key_prefix="leads")
        def get_leads():
            return db.get_all_leads()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera chave única
            cache_key = f"{key_prefix}:{func.__name__}:{advanced_cache._generate_key(*args, **kwargs)}"
            
            # Tenta buscar do cache
            cached_value = advanced_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Executa função e cacheia resultado
            result = func(*args, **kwargs)
            advanced_cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str = None):
    """
    Invalida cache por padrão
    
    Usage:
        invalidate_cache("leads")  # Invalida todos os caches de leads
    """
    advanced_cache.invalidate(pattern)


def get_cache_stats() -> dict:
    """Retorna estatísticas do cache"""
    return advanced_cache.get_stats()