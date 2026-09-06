from unittest.mock import Mock

from xvibe_pocket_tts import demo


def test_local_demo_builds_without_network(monkeypatch):
    monkeypatch.setattr(demo, "RussianTTS", lambda **kw: Mock(auto_accent=True))
    app = demo.create_demo()
    assert app.title == "xVibePocketTTS"
    assert len(app.fns) == 2
