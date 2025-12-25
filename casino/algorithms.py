"""
Game spin algorithms for different times of day and scenarios.
Each algorithm defines the probability distribution for wheel segments.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
import random
from datetime import datetime


class BaseAlgorithm(ABC):
    """Base class for all spin algorithms."""
    
    name: str
    description: str
    
    def __init__(self):
        self.segments = self.get_segments()
    
    @abstractmethod
    def get_segments(self) -> List[Dict]:
        """
        Return list of wheel segments with their properties.
        Each segment must have: id, label, multiplier, color, probability
        """
        pass
    
    @abstractmethod
    def spin(self) -> Dict:
        """
        Perform a spin using this algorithm.
        Returns the selected segment.
        """
        pass
    
    def validate_probabilities(self) -> bool:
        """Validate that probabilities sum to approximately 1.0"""
        total = sum(seg['probability'] for seg in self.segments)
        return abs(total - 1.0) < 0.01


class BalancedAlgorithm(BaseAlgorithm):
    """
    Balanced algorithm - equal probabilities for entertainment.
    Best for peak hours when engagement is high.
    """
    
    name = "Balanced"
    description = "Equal probability distribution - good for peak hours"
    
    def get_segments(self) -> List[Dict]:
        return [
            {'id': 1, 'label': '2x', 'multiplier': 2, 'color': '#D97706', 'probability': 0.125},
            {'id': 2, 'label': '0.5x', 'multiplier': 0.5, 'color': '#6B21A8', 'probability': 0.125},
            {'id': 3, 'label': '3x', 'multiplier': 3, 'color': '#F59E0B', 'probability': 0.125},
            {'id': 4, 'label': 'LOSE', 'multiplier': 0, 'color': '#374151', 'probability': 0.125},
            {'id': 5, 'label': '1.5x', 'multiplier': 1.5, 'color': '#FBBF24', 'probability': 0.125},
            {'id': 6, 'label': '5x', 'multiplier': 5, 'color': '#FCD34D', 'probability': 0.125},
            {'id': 7, 'label': '1x', 'multiplier': 1, 'color': '#78350F', 'probability': 0.125},
            {'id': 8, 'label': '2.5x', 'multiplier': 2.5, 'color': '#B45309', 'probability': 0.125},
        ]
    
    def spin(self) -> Dict:
        """Perform balanced spin."""
        rand = random.random()
        cumulative = 0
        
        for segment in self.segments:
            cumulative += segment['probability']
            if rand <= cumulative:
                return segment.copy()
        
        return self.segments[-1].copy()


class LowProbabilityAlgorithm(BaseAlgorithm):
    """
    Low probability for big wins - designed to be more conservative.
    Best for late hours when fewer players are online (lower spend risk).
    """
    
    name = "Conservative"
    description = "Lower probability for big wins - suitable for low-traffic hours"
    
    def get_segments(self) -> List[Dict]:
        return [
            {'id': 1, 'label': '2x', 'multiplier': 2, 'color': '#D97706', 'probability': 0.18},
            {'id': 2, 'label': '0.5x', 'multiplier': 0.5, 'color': '#6B21A8', 'probability': 0.28},
            {'id': 3, 'label': '3x', 'multiplier': 3, 'color': '#F59E0B', 'probability': 0.06},
            {'id': 4, 'label': 'LOSE', 'multiplier': 0, 'color': '#374151', 'probability': 0.28},
            {'id': 5, 'label': '1.5x', 'multiplier': 1.5, 'color': '#FBBF24', 'probability': 0.10},
            {'id': 6, 'label': '5x', 'multiplier': 5, 'color': '#FCD34D', 'probability': 0.03},
            {'id': 7, 'label': '1x', 'multiplier': 1, 'color': '#78350F', 'probability': 0.04},
            {'id': 8, 'label': '2.5x', 'multiplier': 2.5, 'color': '#B45309', 'probability': 0.03},
        ]
    
    def spin(self) -> Dict:
        """Perform conservative spin."""
        rand = random.random()
        cumulative = 0
        
        for segment in self.segments:
            cumulative += segment['probability']
            if rand <= cumulative:
                return segment.copy()
        
        return self.segments[-1].copy()


class GenerousAlgorithm(BaseAlgorithm):
    """
    Generous algorithm - higher probability for wins and multipliers.
    Best for promotional periods or when you want to attract players.
    """
    
    name = "Generous"
    description = "Higher win probability - good for promotions and weekends"
    
    def get_segments(self) -> List[Dict]:
        return [
            {'id': 1, 'label': '2x', 'multiplier': 2, 'color': '#D97706', 'probability': 0.15},
            {'id': 2, 'label': '0.5x', 'multiplier': 0.5, 'color': '#6B21A8', 'probability': 0.15},
            {'id': 3, 'label': '3x', 'multiplier': 3, 'color': '#F59E0B', 'probability': 0.12},
            {'id': 4, 'label': 'LOSE', 'multiplier': 0, 'color': '#374151', 'probability': 0.15},
            {'id': 5, 'label': '1.5x', 'multiplier': 1.5, 'color': '#FBBF24', 'probability': 0.18},
            {'id': 6, 'label': '5x', 'multiplier': 5, 'color': '#FCD34D', 'probability': 0.08},
            {'id': 7, 'label': '1x', 'multiplier': 1, 'color': '#78350F', 'probability': 0.10},
            {'id': 8, 'label': '2.5x', 'multiplier': 2.5, 'color': '#B45309', 'probability': 0.07},
        ]
    
    def spin(self) -> Dict:
        """Perform generous spin."""
        rand = random.random()
        cumulative = 0
        
        for segment in self.segments:
            cumulative += segment['probability']
            if rand <= cumulative:
                return segment.copy()
        
        return self.segments[-1].copy()


class PeakHourAlgorithm(BaseAlgorithm):
    """
    Peak hour algorithm - optimized for high-traffic periods.
    More frequent small wins to keep players engaged.
    """
    
    name = "Peak Hour"
    description = "Optimized for high-traffic periods with frequent small wins"
    
    def get_segments(self) -> List[Dict]:
        return [
            {'id': 1, 'label': '2x', 'multiplier': 2, 'color': '#D97706', 'probability': 0.20},
            {'id': 2, 'label': '0.5x', 'multiplier': 0.5, 'color': '#6B21A8', 'probability': 0.15},
            {'id': 3, 'label': '3x', 'multiplier': 3, 'color': '#F59E0B', 'probability': 0.08},
            {'id': 4, 'label': 'LOSE', 'multiplier': 0, 'color': '#374151', 'probability': 0.18},
            {'id': 5, 'label': '1.5x', 'multiplier': 1.5, 'color': '#FBBF24', 'probability': 0.22},
            {'id': 6, 'label': '5x', 'multiplier': 5, 'color': '#FCD34D', 'probability': 0.04},
            {'id': 7, 'label': '1x', 'multiplier': 1, 'color': '#78350F', 'probability': 0.08},
            {'id': 8, 'label': '2.5x', 'multiplier': 2.5, 'color': '#B45309', 'probability': 0.05},
        ]
    
    def spin(self) -> Dict:
        """Perform peak hour spin."""
        rand = random.random()
        cumulative = 0
        
        for segment in self.segments:
            cumulative += segment['probability']
            if rand <= cumulative:
                return segment.copy()
        
        return self.segments[-1].copy()


class LateNightAlgorithm(BaseAlgorithm):
    """
    Late night algorithm - more conservative, longer engagement.
    Fewer big wins but keeps players interested.
    """
    
    name = "Late Night"
    description = "Conservative late-night algorithm for sustained engagement"
    
    def get_segments(self) -> List[Dict]:
        return [
            {'id': 1, 'label': '2x', 'multiplier': 2, 'color': '#D97706', 'probability': 0.16},
            {'id': 2, 'label': '0.5x', 'multiplier': 0.5, 'color': '#6B21A8', 'probability': 0.30},
            {'id': 3, 'label': '3x', 'multiplier': 3, 'color': '#F59E0B', 'probability': 0.04},
            {'id': 4, 'label': 'LOSE', 'multiplier': 0, 'color': '#374151', 'probability': 0.30},
            {'id': 5, 'label': '1.5x', 'multiplier': 1.5, 'color': '#FBBF24', 'probability': 0.12},
            {'id': 6, 'label': '5x', 'multiplier': 5, 'color': '#FCD34D', 'probability': 0.02},
            {'id': 7, 'label': '1x', 'multiplier': 1, 'color': '#78350F', 'probability': 0.04},
            {'id': 8, 'label': '2.5x', 'multiplier': 2.5, 'color': '#B45309', 'probability': 0.02},
        ]
    
    def spin(self) -> Dict:
        """Perform late night spin."""
        rand = random.random()
        cumulative = 0
        
        for segment in self.segments:
            cumulative += segment['probability']
            if rand <= cumulative:
                return segment.copy()
        
        return self.segments[-1].copy()


class AggressiveLosingStreakAlgorithm(BaseAlgorithm):
    """
    Aggressive losing streak algorithm - designed to test system resilience.
    Very high probability of losses and low-value outcomes.
    Useful for stress testing and demonstrating responsible gaming features.
    """
    
    name = "Aggressive Losing Streak"
    description = "High loss probability for stress testing and edge case handling"
    
    def get_segments(self) -> List[Dict]:
        return [
            {'id': 1, 'label': '2x', 'multiplier': 2, 'color': '#D97706', 'probability': 0.05},
            {'id': 2, 'label': '0.5x', 'multiplier': 0.5, 'color': '#6B21A8', 'probability': 0.45},
            {'id': 3, 'label': '3x', 'multiplier': 3, 'color': '#F59E0B', 'probability': 0.01},
            {'id': 4, 'label': 'LOSE', 'multiplier': 0, 'color': '#374151', 'probability': 0.40},
            {'id': 5, 'label': '1.5x', 'multiplier': 1.5, 'color': '#FBBF24', 'probability': 0.05},
            {'id': 6, 'label': '5x', 'multiplier': 5, 'color': '#FCD34D', 'probability': 0.01},
            {'id': 7, 'label': '1x', 'multiplier': 1, 'color': '#78350F', 'probability': 0.02},
            {'id': 8, 'label': '2.5x', 'multiplier': 2.5, 'color': '#B45309', 'probability': 0.01},
        ]
    
    def spin(self) -> Dict:
        """Perform aggressive losing streak spin."""
        rand = random.random()
        cumulative = 0
        
        for segment in self.segments:
            cumulative += segment['probability']
            if rand <= cumulative:
                return segment.copy()
        
        return self.segments[-1].copy()


# Registry of all available algorithms
ALGORITHM_REGISTRY = {
    'balanced': BalancedAlgorithm,
    'conservative': LowProbabilityAlgorithm,
    'generous': GenerousAlgorithm,
    'peak_hour': PeakHourAlgorithm,
    'late_night': LateNightAlgorithm,
    'aggressive_losing_streak': AggressiveLosingStreakAlgorithm,
}


def get_algorithm(algorithm_key: str) -> BaseAlgorithm:
    """
    Get an algorithm instance by key.
    
    Args:
        algorithm_key: Key from ALGORITHM_REGISTRY
    
    Returns:
        BaseAlgorithm instance
    
    Raises:
        ValueError: If algorithm_key is not found
    """
    if algorithm_key not in ALGORITHM_REGISTRY:
        raise ValueError(f"Algorithm '{algorithm_key}' not found. Available: {list(ALGORITHM_REGISTRY.keys())}")
    
    return ALGORITHM_REGISTRY[algorithm_key]()


def get_all_algorithms() -> List[Dict]:
    """Get list of all available algorithms with metadata."""
    algorithms = []
    for key, AlgorithmClass in ALGORITHM_REGISTRY.items():
        instance = AlgorithmClass()
        algorithms.append({
            'key': key,
            'name': instance.name,
            'description': instance.description,
        })
    return algorithms
