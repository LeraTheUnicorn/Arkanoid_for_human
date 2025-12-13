#!/usr/bin/env python3
"""
Тесты для GameController - основной игровой логики.
"""

import sys
import os
import pygame
from typing import List

# Добавляем родительскую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.game_controllers import GameController
from game.game_models import Ball, Paddle, GameState
from game.settings import SettingsManager
from game.game_config import SCREEN_WIDTH, SCREEN_HEIGHT


def test_build_bricks() -> bool:
    """Тест создания кирпичей"""
    print("Testing GameController.build_bricks()")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    settings = SettingsManager()
    
    controller = GameController(game_state, ball, paddle, settings)
    bricks = controller.build_bricks()
    
    assert len(bricks) > 0, "Should create bricks"
    assert all(isinstance(brick, pygame.Rect) for brick in bricks), "All bricks should be Rect objects"
    
    # Проверяем, что кирпичи не выходят за границы экрана
    for brick in bricks:
        assert brick.left >= 0, "Brick should not be outside left boundary"
        assert brick.right <= SCREEN_WIDTH, "Brick should not be outside right boundary"
        assert brick.top >= 0, "Brick should not be above screen"
    
    pygame.quit()
    print("  ✓ Build bricks tests passed")
    return True


def test_ball_paddle_collision() -> bool:
    """Тест столкновения мяча с платформой"""
    print("Testing GameController.check_ball_paddle_collision()")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    settings = SettingsManager()
    
    controller = GameController(game_state, ball, paddle, settings)
    
    # Позиционируем мяч над платформой, движущийся вниз
    ball.rect.centerx = paddle.rect.centerx
    ball.rect.bottom = paddle.rect.top + 5
    ball.vel_y = 5  # Движется вниз
    
    collision = controller.check_ball_paddle_collision()
    assert collision == True, "Should detect collision when ball hits paddle from above"
    
    # Мяч движется вверх - не должно быть столкновения
    ball.vel_y = -5
    collision = controller.check_ball_paddle_collision()
    assert collision == False, "Should not detect collision when ball moves upward"
    
    # Мяч далеко от платформы
    ball.rect.centery = 100
    collision = controller.check_ball_paddle_collision()
    assert collision == False, "Should not detect collision when ball is far from paddle"
    
    pygame.quit()
    print("  ✓ Ball-paddle collision tests passed")
    return True


def test_handle_ball_paddle_collision() -> bool:
    """Тест обработки столкновения мяча с платформой"""
    print("Testing GameController.handle_ball_paddle_collision()")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    settings = SettingsManager()
    
    controller = GameController(game_state, ball, paddle, settings)
    
    # Позиционируем мяч для столкновения
    ball.rect.centerx = paddle.rect.centerx
    ball.rect.bottom = paddle.rect.top + 5
    ball.vel_y = 5
    initial_vel_y = ball.vel_y
    
    controller.handle_ball_paddle_collision()
    
    # Мяч должен отскочить
    assert ball.vel_y < 0, "Ball should bounce upward after paddle collision"
    assert ball._just_bounced == True, "Bounce flag should be set"
    
    pygame.quit()
    print("  ✓ Handle ball-paddle collision tests passed")
    return True


def test_ball_brick_collision() -> bool:
    """Тест столкновения мяча с кирпичами"""
    print("Testing GameController.check_ball_brick_collision()")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    settings = SettingsManager()
    
    controller = GameController(game_state, ball, paddle, settings)
    game_state.bricks = controller.build_bricks()
    
    # Позиционируем мяч для столкновения с первым кирпичом
    if game_state.bricks:
        brick = game_state.bricks[0]
        ball.rect.centerx = brick.centerx
        ball.rect.centery = brick.centery
        
        hit_index = controller.check_ball_brick_collision()
        assert hit_index is not None, "Should detect collision with brick"
        assert hit_index == 0, "Should return index of hit brick"
    
    # Мяч далеко от кирпичей
    ball.rect.centery = SCREEN_HEIGHT - 100
    hit_index = controller.check_ball_brick_collision()
    assert hit_index is None, "Should not detect collision when ball is far from bricks"
    
    pygame.quit()
    print("  ✓ Ball-brick collision tests passed")
    return True


def test_handle_ball_brick_collision() -> bool:
    """Тест обработки столкновения мяча с кирпичом"""
    print("Testing GameController.handle_ball_brick_collision()")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    settings = SettingsManager()
    
    controller = GameController(game_state, ball, paddle, settings)
    game_state.bricks = controller.build_bricks()
    initial_brick_count = len(game_state.bricks)
    initial_score = game_state.score
    
    # Позиционируем мяч для столкновения
    if game_state.bricks:
        brick = game_state.bricks[0]
        ball.rect.centerx = brick.centerx
        ball.rect.centery = brick.centery
        initial_vel_y = ball.vel_y
        
        destroyed_brick = controller.handle_ball_brick_collision()
        
        assert destroyed_brick is not None, "Should return destroyed brick"
        assert len(game_state.bricks) == initial_brick_count - 1, "Brick should be removed"
        assert game_state.score == initial_score + 1, "Score should increase"
        assert ball.vel_y == -initial_vel_y, "Ball should bounce vertically"
    
    pygame.quit()
    print("  ✓ Handle ball-brick collision tests passed")
    return True


def test_ball_out_of_bounds() -> bool:
    """Тест выхода мяча за границы"""
    print("Testing GameController.check_ball_out_of_bounds()")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    settings = SettingsManager()
    
    controller = GameController(game_state, ball, paddle, settings)
    
    # Мяч в пределах экрана
    ball.rect.top = SCREEN_HEIGHT - 100
    out_of_bounds = controller.check_ball_out_of_bounds()
    assert out_of_bounds == False, "Should not detect out of bounds when ball is on screen"
    
    # Мяч за нижней границей
    ball.rect.top = SCREEN_HEIGHT + 10
    out_of_bounds = controller.check_ball_out_of_bounds()
    assert out_of_bounds == True, "Should detect out of bounds when ball is below screen"
    
    pygame.quit()
    print("  ✓ Ball out of bounds tests passed")
    return True


def test_handle_ball_out_of_bounds() -> bool:
    """Тест обработки выхода мяча за границы"""
    print("Testing GameController.handle_ball_out_of_bounds()")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    settings = SettingsManager()
    
    controller = GameController(game_state, ball, paddle, settings)
    
    initial_lives = game_state.lives_left
    
    # Мяч за границами
    ball.rect.top = SCREEN_HEIGHT + 10
    controller.handle_ball_out_of_bounds()
    
    assert game_state.lives_left == initial_lives - 1, "Lives should decrease"
    assert ball.vel_y == 0, "Ball should stop"
    assert game_state.game_started == False, "Game should pause"
    
    # Проверяем game over
    game_state.lives_left = 1
    ball.rect.top = SCREEN_HEIGHT + 10
    controller.handle_ball_out_of_bounds()
    
    assert game_state.game_over == True, "Game should be over when lives reach 0"
    
    pygame.quit()
    print("  ✓ Handle ball out of bounds tests passed")
    return True


def test_reset_game() -> bool:
    """Тест сброса игры"""
    print("Testing GameController.reset_game()")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    settings = SettingsManager()
    
    controller = GameController(game_state, ball, paddle, settings)
    
    # Изменяем состояние
    game_state.score = 100
    game_state.lives_left = 1
    game_state.game_started = True
    game_state.game_over = True
    
    controller.reset_game()
    
    assert game_state.score == 0, "Score should be reset"
    assert game_state.lives_left == 3, "Lives should be reset"
    assert game_state.game_started == False, "Game should not be started"
    assert game_state.game_over == False, "Game should not be over"
    assert len(game_state.bricks) > 0, "Bricks should be created"
    assert ball.vel_y == 0, "Ball should be stopped"
    
    pygame.quit()
    print("  ✓ Reset game tests passed")
    return True


def main() -> bool:
    """Запуск всех тестов"""
    print("=== Testing Game Controller ===\n")
    
    tests = [
        test_build_bricks,
        test_ball_paddle_collision,
        test_handle_ball_paddle_collision,
        test_ball_brick_collision,
        test_handle_ball_brick_collision,
        test_ball_out_of_bounds,
        test_handle_ball_out_of_bounds,
        test_reset_game,
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
        print("✓ All game controller tests passed!")
        return True
    else:
        print(f"✗ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

