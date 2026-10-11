# coding=utf-8
"""Offline guard: fail loudly if a non-network test reaches the network.

体彩/福彩接口对境外 IP 有 WAF（GitHub 跑道 HTTP 567），任何被离线测试
悄悄触发的真实请求只会在 CI 上随机爆炸。非 `network` 标记的用例一律阻断
`requests.Session.get/send`；确需联网的用例请显式打 `@pytest.mark.network`。
"""

import pytest


@pytest.fixture(autouse=True)
def _offline_guard(monkeypatch, request):
    if request.node.get_closest_marker("network"):
        return

    def _blocked(*args, **kwargs):
        raise AssertionError(
            "offline tests must not hit the network; mock the client or mark the test with @pytest.mark.network"
        )

    monkeypatch.setattr("requests.Session.get", _blocked)
    monkeypatch.setattr("requests.Session.send", _blocked)
