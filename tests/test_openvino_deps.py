def test_openvino_imports():
    import openvino
    assert openvino.__version__ is not None
    assert openvino.Core() is not None

