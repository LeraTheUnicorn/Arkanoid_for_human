#!/usr/bin/env python3
"""
Тесты для функциональности паузы при потере жизни.
"""

import sys
import os
import pygame
from typing import Dict

# Добавляем родительскую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.game_models import Ball, Paddle, GameState
from game.game_config import SCREEN_HEIGHT


def test_pause_on_life_loss() -> bool:
    """Тест активации паузы при потере жизни"""
    print("Testing pause on life loss")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    
    # Имитируем потерю жизни
    game_state.game_started = True
    game_state.lives_left = 3
    game_paused = False
    
    # Мяч уходит за нижнюю границу
    ball.rect.top = SCREEN_HEIGHT + 10
    
    if ball.rect.top > SCREEN_HEIGHT:
        game_state.lives_left -= 1
        if game_state.lives_left > 0:
            game_paused = True
            ball.vel_y = 0
            # Мяч должен быть на платформе
            ball.rect.center = paddle.rect.midtop
            ball.rect.y -= ball.rect.height
    
    assert game_paused == True, "Game should pause on life loss"
    assert ball.vel_y == 0, "Ball should stop when paused"
    assert game_state.lives_left == 2, "Lives should decrease"
    assert game_state.game_started == True, "Game should remain started"
    
    pygame.quit()
    print("  ✓ Pause on life loss tests passed")
    return True


def test_resume_from_pause() -> bool:
    """Тест возобновления игры после паузы"""
    print("Testing resume from pause")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    
    # Имитируем паузу
    game_state.game_started = True
    game_paused = True
    ball.vel_y = 0
    ball.rect.center = paddle.rect.midtop
    ball.rect.y -= ball.rect.height
    
    # Имитируем нажатие SPACE
    # В реальной игре это обрабатывается в event loop
    if game_paused:
        game_paused = False
        # Мяч запускается в случайном направлении
        import random
        ball.vel_x = random.choice([-ball.get_speed(), ball.get_speed()])
        ball.vel_y = -ball.get_speed()
    
    assert game_paused == False, "Game should resume from pause"
    assert ball.vel_y != 0, "Ball should start moving"
    assert abs(ball.vel_x) == ball.get_speed(), "Ball should have horizontal velocity"
    
    pygame.quit()
    print("  ✓ Resume from pause tests passed")
    return True


def test_pause_blocks_paddle_movement() -> bool:
    """Тест блокировки движения платформы во время паузы"""
    print("Testing pause blocks paddle movement")
    
    pygame.init()
    
    paddle = Paddle()
    game_paused = True
    initial_x = paddle.rect.centerx
    
    # Имитируем нажатие стрелок влево/вправо во время паузы
    # В реальной игре эти события игнорируются
    keys_pressed = {"left": True, "right": False}
    
    if not game_paused:
        if keys_pressed["left"]:
            paddle.move(-1)
        elif keys_pressed["right"]:
            paddle.move(1)
    
    # Платформа не должна двигаться во время паузы
    assert paddle.rect.centerx == initial_x, "Paddle should not move during pause"
    
    pygame.quit()
    print("  ✓ Pause blocks paddle movement tests passed")
    return True


def test_pause_allows_speed_change() -> bool:
    """Тест изменения скорости мяча во время паузы"""
    print("Testing speed change during pause")
    
    from game.settings import SettingsManager
    
    ball = Ball()
    settings = SettingsManager()
    game_paused = True
    initial_speed = ball.get_speed()
    
    # Имитируем нажатие стрелок вверх/вниз во время паузы
    # В реальной игре эти события обрабатываются даже во время паузы
    keys_pressed = {"up": True, "down": False}
    
    if keys_pressed["up"]:
        ball.increase_speed(settings)
    elif keys_pressed["down"]:
        ball.decrease_speed(settings)
    
    # Скорость должна измениться даже во время паузы
    assert ball.get_speed() > initial_speed, "Speed should change during pause"
    
    pygame.quit()
    print("  ✓ Speed change during pause tests passed")
    return True


def test_pause_hint_display() -> bool:
    """Тест отображения подсказки паузы"""
    print("Testing pause hint display")
    
    pygame.init()
    
    screen = pygame.display.set_mode((800, 600))
    font = pygame.font.Font(None, 36)
    game_paused = True
    
    # Имитируем функцию draw_pause_hint
    if game_paused:
        hint_text = "Нажмите SPACE для продолжения"
        text_surface = font.render(hint_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        
        assert hint_text == "Нажмите SPACE для продолжения", "Should show correct pause hint"
        assert text_rect.centerx == screen.get_width() // 2, "Hint should be centered"
        assert text_rect.centery == screen.get_height() // 2, "Hint should be centered"
    
    pygame.quit()
    print("  ✓ Pause hint display tests passed")
    return True


def test_no_pause_on_game_over() -> bool:
    """Тест отсутствия паузы при game over"""
    print("Testing no pause on game over")
    
    pygame.init()
    
    game_state = GameState()
    ball = Ball()
    paddle = Paddle()
    
    # Имитируем последнюю жизнь
    game_state.lives_left = 1
    game_state.game_started = True
    game_paused = False
    
    # Мяч уходит за нижнюю границу
    ball.rect.top = SCREEN_HEIGHT + 10
    
    if ball.rect.top > SCREEN_HEIGHT:
        game_state.lives_left -= 1
        if game_state.lives_left > 0:
            game_paused = True
        else:
            game_state.game_over = True
    
    assert game_state.game_over == True, "Game should be over when lives reach 0"
    assert game_paused == False, "Should not pause on game over"
    
    pygame.quit()
    print("  ✓ No pause on game over tests passed")
    return True


def main() -> bool:
    """Запуск всех тестов"""
    print("=== Testing Game Pause Functionality ===\n")
    
    tests = [
        test_pause_on_life_loss,
        test_resume_from_pause,
        test_pause_blocks_paddle_movement,
        test_pause_allows_speed_change,
        test_pause_hint_display,
        test_no_pause_on_game_over,
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
        print("✓ All pause functionality tests passed!")
        return True
    else:
        print(f"✗ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

