def main():
    print("hi")

def test__mine_minesweeper_():
    import minesweeper
    b = minesweeper.Board(5, 5, 3)
    b2 = b.generate_gameboard(b.grid, 3, 42)
    assert sum(sum(r) for r in b2) == 3


def test_health_endpoint():
    import health_endpoint
    status, body = health_endpoint.health()
    assert status == 200
    assert body == {"status": "ok"}


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
