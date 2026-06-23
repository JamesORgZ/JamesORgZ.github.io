def test_app_module_imports():
    import james_srt_studio.app as app

    assert app.main is not None
