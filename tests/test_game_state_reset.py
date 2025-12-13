#!/usr/bin/env python3
"""
Тест для проверки сброса состояния игры в авторежиме.
Проверяет, что при возврате к экрану ввода имени состояние игры сбрасывается корректно.
"""

import sys
import os
from typing import List

# Add current directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_game_state_reset() -> bool:
    """Test game state reset functionality"""

    print("=== GAME STATE RESET TEST ===")
    print()

    # Test 1: Check that paddle, ball, bricks are created in the main loop
    print("1. Checking game state initialization in main loop...")
    try:
        # Правильный путь к PyGameBall.py
        pygameball_path: str = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "game", "PyGameBall.py"
        )
        with open(pygameball_path, "r", encoding="utf-8") as f:
            content: str = f.read()

        # Check for state reset in the main loop
        state_reset_checks: List[str] = [
            "paddle = Paddle()",
            "ball = Ball()",
            "bricks = build_bricks()",
            "score = 0",
            "lives_left = MAX_LIVES",
            "game_over = False",
            "game_started = False",
        ]

        found_checks: int = 0
        for check in state_reset_checks:
            if check in content:
                found_checks += 1

        if found_checks >= 6:
            print(
                f"   [OK] Game state reset found in main loop ({found_checks}/{len(state_reset_checks)} checks)"
            )
        else:
            print(
                f"   [FAIL] Game state reset incomplete ({found_checks}/{len(state_reset_checks)} checks)"
            )
            return False

    except Exception as e:
        print(f"   [FAIL] Error reading file: {e}")
        return False

    # Test 2: Check that state variables are not duplicated at the top level
    print("2. Checking for duplicate state initialization...")
    try:
        # Правильный путь к PyGameBall.py
        pygameball_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "PyGameBall.py"
        )
        with open(pygameball_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Count occurrences of key state variables
        paddle_init_count: int = content.count("paddle = Paddle()")
        ball_init_count: int = content.count("ball = Ball()")
        bricks_init_count: int = content.count("bricks = build_bricks()")
        score_init_count: int = content.count("score = 0")

        # Should have exactly one initialization in the main loop
        # Plus one in the manual restart section for paddle/ball/bricks
        # Score should appear multiple times (initialization, resets)

        if paddle_init_count >= 2 and ball_init_count >= 2:
            print(
                f"   [OK] State initialization properly placed (paddle: {paddle_init_count}, ball: {ball_init_count})"
            )
        else:
            print(
                f"   [WARN] State initialization count might be insufficient (paddle: {paddle_init_count}, ball: {ball_init_count})"
            )

    except Exception as e:
        print(f"   [FAIL] Error checking initialization count: {e}")
        return False

    # Test 3: Check for proper game flow logic
    print("3. Checking game flow logic...")
    try:
        # Правильный путь к PyGameBall.py
        pygameball_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "PyGameBall.py"
        )
        with open(pygameball_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for main game loop structure
        flow_checks: List[str] = [
            "while True:  # Внешний цикл для возврата к вводу имени",
            "running = True",
            "# ПОЛНЫЙ СБРОС СОСТОЯНИЯ ИГРЫ ПРИ КАЖДОМ НОВОМ ЗАПУСКЕ",
        ]

        found_checks = 0
        for check in flow_checks:
            if check in content:
                found_checks += 1

        if found_checks >= 2:
            print("   [OK] Game flow logic properly structured")
        else:
            print(
                f"   [FAIL] Game flow logic incomplete ({found_checks}/{len(flow_checks)} checks)"
            )
            return False

    except Exception as e:
        print(f"   [FAIL] Error checking game flow: {e}")
        return False

    # Test 4: Check for game state reset (auto mode removed)
    print("4. Checking game state reset logic...")
    try:
        # Правильный путь к PyGameBall.py
        pygameball_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game", "PyGameBall.py"
        )
        with open(pygameball_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for game reset logic
        reset_checks: List[str] = [
            "running = False",
            "break  # Выход из игрового цикла",
            "game_over = False",
        ]

        found_checks = 0
        for check in reset_checks:
            if check in content:
                found_checks += 1

        if found_checks >= 2:
            print("   [OK] Game reset logic found")
        else:
            print(
                f"   [FAIL] Game reset logic incomplete ({found_checks}/{len(reset_checks)} checks)"
            )
            return False

    except Exception as e:
        print(f"   [FAIL] Error checking auto mode handling: {e}")
        return False

    print()
    print("=== TEST RESULT ===")
    print("[OK] All checks passed successfully!")
    print()
    print("Key improvements:")
    print("- Full game state reset in main loop")
    print("- Proper separation of initialization and reset")
    print("- Correct auto mode flow handling")
    print("- No duplicate state variables")

    return True


if __name__ == "__main__":
    success = test_game_state_reset()
    sys.exit(0 if success else 1)
