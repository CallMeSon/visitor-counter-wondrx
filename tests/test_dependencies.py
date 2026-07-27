def test_onnx_imports():
    import onnx
    import onnxruntime
    assert onnx.__version__ is not None
    assert onnxruntime.__version__ is not None
