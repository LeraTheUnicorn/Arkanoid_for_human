#!/usr/bin/env python3
"""
Тесты для игровых моделей (Ball, Paddle, GameState).
"""

import sys
import os
import pygame
from typing import List

# Добавляем родительскую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.game_models import Ball, Paddle, GameState
from game.game_config import SCREEN_WIDTH, SCREEN_HEIGHT, BALL_SIZE, PADDLE_WIDTH


def test_ball_update_wall_collisions() -> bool:
    """Тест столкновения мяча со стенами"""
    print("Testing Ball.update() - wall collisions")
    
    pygame.init()
    
    ball = Ball()
    initial_x = ball.rect.centerx
    initial_y = ball.rect.centery
    
    # Устанавливаем мяч у левой стены
    ball.rect.centerx = BALL_SIZE // 2
    ball.vel_x = -5  # Движется влево
    
    ball.update()
    
    # Мяч должен отскочить
    assert ball.vel_x > 0, "Ball should bounce from left wall"
    assert ball.rect.centerx >= BALL_SIZE // 2, "Ball should not go through left wall"
    
    # Устанавливаем мяч у правой стены
    ball.rect.centerx = SCREEN_WIDTH - BALL_SIZE // 2
    ball.vel_x = 5  # Движется вправо
    
    ball.update()
    
    # Мяч должен отскочить
    assert ball.vel_x < 0, "Ball should bounce from right wall"
    assert ball.rect.centerx <= SCREEN_WIDTH - BALL_SIZE // 2, "Ball should not go through right wall"
    
    # Устанавливаем мяч у потолка
    ball.rect.centery = BALL_SIZE // 2
    ball.vel_y = -5  # Движется вверх
    
    ball.update()
    
    # Мяч должен отскочить
    assert ball.vel_y > 0, "Ball should bounce from ceiling"
    assert ball.rect.centery >= BALL_SIZE // 2, "Ball should not go through ceiling"
    
    pygame.quit()
    print("  ✓ Wall collision tests passed")
    return True


def test_ball_bounce_vertical() -> bool:
    """Тест вертикального отскока мяча"""
    print("Testing Ball.bounce_vertical()")
    
    ball = Ball()
    
    # Тест отскока когда мяч движется вниз
    ball.vel_y = 5
    initial_vel_y = ball.vel_y
    ball.bounce_vertical()
    
    assert ball.vel_y == -initial_vel_y, "Ball should reverse vertical velocity"
    
    # Тест отскока когда мяч движется вверх
    ball.vel_y = -5
    initial_vel_y = ball.vel_y
    ball.bounce_vertical()
    
    assert ball.vel_y == -initial_vel_y, "Ball should reverse vertical velocity"
    
    # Тест отскока когда мяч неподвижен
    ball.vel_y = 0
    ball.bounce_vertical()
    
    assert ball.vel_y == -ball.current_speed, "Ball should start moving up when vel_y is 0"
    
    print("  ✓ Bounce vertical tests passed")
    return True


def test_ball_reset() -> bool:
    """Тест сброса мяча на платформу"""
    print("Testing Ball.reset()")
    
    pygame.init()
    
    paddle = Paddle()
    ball = Ball()
    
    # Перемещаем мяч в случайное место
    ball.rect.centerx = 100
    ball.rect.centery = 200
    ball.vel_x = 10
    ball.vel_y = 10
    
    ball.reset(paddle.rect)
    
    # Мяч должен быть над платформой
    assert ball.rect.centerx == paddle.rect.centerx, "Ball should be centered on paddle"
    assert ball.rect.centery < paddle.rect.top, "Ball should be above paddle"
    assert ball.vel_y == -ball.current_speed, "Ball should move upward"
    assert abs(ball.vel_x) == ball.current_speed, "Ball should have horizontal velocity"
    
    pygame.quit()
    print("  ✓ Reset tests passed")
    return True


def test_ball_speed_limits() -> bool:
    """Тест ограничений скорости мяча"""
    print("Testing Ball speed limits")
    
    from game.settings import SettingsManager
    
    ball = Ball()
    settings = SettingsManager()
    
    # Устанавливаем минимальную скорость
    ball.set_speed(1, settings)
    assert ball.get_speed() == 1, "Should be able to set speed to 1"
    
    # Пытаемся уменьшить ниже минимума
    ball.decrease_speed(settings)
    assert ball.get_speed() == 1, "Speed should not go below 1"
    
    # Устанавливаем максимальную скорость
    ball.set_speed(10, settings)
    assert ball.get_speed() == 10, "Should be able to set speed to 10"
    
    # Пытаемся увеличить выше максимума
    ball.increase_speed(settings)
    assert ball.get_speed() == 10, "Speed should not go above 10"
    
    print("  ✓ Speed limit tests passed")
    return True


def test_paddle_move_boundaries() -> bool:
    """Тест движения платформы с границами"""
    print("Testing Paddle.move() - boundaries")
    
    pygame.init()
    
    paddle = Paddle()
    
    # Движение влево до границы
    initial_x = paddle.rect.centerx
    for _ in range(1000):  # Много движений влево
        paddle.move(-1)
    
    # Платформа не должна выйти за левую границу
    assert paddle.rect.centerx >= PADDLE_WIDTH // 2, "Paddle should not go beyond left boundary"
    
    # Движение вправо до границы
    for _ in range(1000):  # Много движений вправо
        paddle.move(1)
    
    # Платформа не должна выйти за правую границу
    assert paddle.rect.centerx <= SCREEN_WIDTH - PADDLE_WIDTH // 2, "Paddle should not go beyond right boundary"
    
    pygame.quit()
    print("  ✓ Paddle boundary tests passed")
    return True


def test_paddle_move_direction() -> bool:
    """Тест направления движения платформы"""
    print("Testing Paddle.move() - direction")
    
    pygame.init()
    
    paddle = Paddle()
    initial_centerx = paddle.rect.centerx
    
    # Движение вправо
    paddle.move(1)
    assert paddle.rect.centerx > initial_centerx or paddle.rect.centerx == initial_centerx, "Paddle should move right or stay at boundary with direction=1"
    
    # Движение влево
    new_centerx = paddle.rect.centerx
    paddle.move(-1)
    assert paddle.rect.centerx < new_centerx or paddle.rect.centerx == new_centerx, "Paddle should move left or stay at boundary with direction=-1"
    
    pygame.quit()
    print("  ✓ Paddle direction tests passed")
    return True


def test_game_state_reset() -> bool:
    """Тест сброса состояния игры"""
    print("Testing GameState.reset()")
    
    state = GameState()
    
    # Изменяем состояние
    state.score = 100
    state.lives_left = 1
    state.game_started = True
    state.game_over = True
    state.bricks = [pygame.Rect(0, 0, 10, 10)]
    state.game_start_time = 123.45
    
    # Сбрасываем
    state.reset()
    
    assert state.score == 0, "Score should be reset to 0"
    assert state.lives_left == 3, "Lives should be reset to 3"
    assert state.game_started == False, "game_started should be False"
    assert state.game_over == False, "game_over should be False"
    assert len(state.bricks) == 0, "Bricks should be empty"
    assert state.game_start_time == 0.0, "game_start_time should be 0.0"
    
    print("  ✓ GameState reset tests passed")
    return True


def main() -> bool:
    """Запуск всех тестов"""
    print("=== Testing Game Models ===\n")
    
    tests = [
        test_ball_update_wall_collisions,
        test_ball_bounce_vertical,
        test_ball_reset,
        test_ball_speed_limits,
        test_paddle_move_boundaries,
        test_paddle_move_direction,
        test_game_state_reset,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  ✗ {test_func.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"  ✗ {test_func.__name__} failed with error: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print(f"=== Results: {passed}/{len(tests)} tests passed ===")
    
    if failed == 0:
        print("✓ All game models tests passed!")
        return True
    else:
        print(f"✗ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

