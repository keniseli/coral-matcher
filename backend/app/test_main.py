import pytest
import numpy as np
import cv2
from vision import apply_underwater_corrections
from embedding import generate_vector_embedding

def test_resnet_feature_vector_dimensions():
    """
    Creates an artificial 300x300 canvas to ensure the PyTorch 
    engine extracts exactly 512 descriptive parameters.
    """
    # Create mock canvas matrix
    mock_coral_canvas = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    
    # Generate signature array
    vector_output = generate_vector_embedding(mock_coral_canvas)
    
    assert isinstance(vector_output, list)
    assert len(vector_output) == 512
    assert isinstance(vector_output[0], float)


def test_image_processing_math_extensions():
    """
    Generates a generic dummy 100x100 dark blue pixel array matrix 
    to verify our color spectrum balancing formula functions without crashing.
    """
    # Create an artificial raw deep blue image matrix
    dummy_blue_img = np.zeros((100, 100, 3), dtype=np.uint8)
    dummy_blue_img[:, :, 0] = 180  # Intense Blue Channel
    dummy_blue_img[:, :, 1] = 80   # Moderate Green Channel
    dummy_blue_img[:, :, 2] = 20   # Stripped down weak Red Channel

    # Execute processing execution
    output_matrix = apply_underwater_corrections(dummy_blue_img)

    assert output_matrix is not None
    assert output_matrix.shape == (100, 100, 3)
    
    # Assert that the suppressed red channel (index 2) was lifted by the algorithm
    assert int(output_matrix[50, 50, 2]) > 20

def test_empty_matrix_guards():
    """
    Verifies the engine throws a proper exception validation error when fed null bytes.
    """
    empty_matrix = np.array([], dtype=np.uint8)
    with pytest.raises(ValueError, match="Empty image matrix passed"):
        apply_underwater_corrections(empty_matrix)
