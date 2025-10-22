"""Pytest configuration and fixtures."""

import pytest
import numpy as np
import torch


@pytest.fixture(scope="session")
def random_seed():
    """Set random seeds for reproducibility."""
    np.random.seed(42)
    torch.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(42)


@pytest.fixture
def sample_rgb_image():
    """Generate a sample RGB image."""
    return np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)


@pytest.fixture
def sample_grayscale_image():
    """Generate a sample grayscale image."""
    return np.random.randint(0, 255, (256, 256), dtype=np.uint8)


@pytest.fixture
def sample_batch_images():
    """Generate a batch of sample images."""
    return np.random.randint(0, 255, (4, 256, 256, 3), dtype=np.uint8)
