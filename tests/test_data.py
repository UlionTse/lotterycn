# coding=utf-8
# author=Ulion.Tse

from lotterycn.data import load_random_data, lottery_pool

CL_COLS = ["lottery_name", "lottery_order", "lottery_date", "lottery_red", "lottery_blue"]


def test_lottery_pool():
    assert lottery_pool == ("dlt", "pls", "plw", "qxc", "ssq", "qlc", "kl8", "3d")


def test_load_random_data_shape():
    for lottery_name in lottery_pool:
        frame = load_random_data(lottery_name=lottery_name, amount=3)
        assert len(frame) == 3
        assert list(frame.columns) == CL_COLS
        assert (frame["lottery_name"] == lottery_name).all()
        assert list(frame["lottery_order"]) == [0, 1, 2]


def _split_reds(text):
    return [int(x) for x in str(text).split(",")]


def test_random_number_ranges():
    frame = load_random_data("ssq", amount=5)
    for red, blue in zip(frame["lottery_red"], frame["lottery_blue"]):
        nums = _split_reds(red)
        assert len(nums) == len(set(nums)) == 6
        assert all(1 <= n <= 33 for n in nums)
        assert 1 <= int(blue) <= 16

    frame = load_random_data("dlt", amount=5)
    for red, blue in zip(frame["lottery_red"], frame["lottery_blue"]):
        reds, blues = _split_reds(red), _split_reds(blue)
        assert len(reds) == len(set(reds)) == 5 and all(1 <= n <= 35 for n in reds)
        assert len(blues) == len(set(blues)) == 2 and all(1 <= n <= 12 for n in blues)

    frame = load_random_data("qlc", amount=5)
    for red, blue in zip(frame["lottery_red"], frame["lottery_blue"]):
        reds = _split_reds(red)
        assert len(reds) == len(set(reds)) == 7 and all(1 <= n <= 30 for n in reds)
        assert int(blue) not in reds and 1 <= int(blue) <= 30

    frame = load_random_data("kl8", amount=5)
    for red in frame["lottery_red"]:
        nums = _split_reds(red)
        assert len(nums) == len(set(nums)) == 20
        assert all(1 <= n <= 80 for n in nums)

    for name, count in (("3d", 3), ("pls", 3), ("plw", 5)):
        frame = load_random_data(name, amount=5)
        for red in frame["lottery_red"]:
            nums = _split_reds(red)
            assert len(nums) == count and all(0 <= n <= 9 for n in nums)

    frame = load_random_data("qxc", amount=5)
    for red, blue in zip(frame["lottery_red"], frame["lottery_blue"]):
        reds = _split_reds(red)
        assert len(reds) == 6 and all(0 <= n <= 9 for n in reds)
        assert 0 <= int(blue) <= 14
