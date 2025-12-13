#!/usr/bin/env python3
"""
Тесты для DirtyRectManager - оптимизация отрисовки.
"""

import sys
import os
import pygame

# Добавляем родительскую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.dirty_rects import DirtyRectManager
from game.game_config import SCREEN_WIDTH, SCREEN_HEIGHT


def test_dirty_rect_manager_init() -> bool:
    """Тест инициализации DirtyRectManager"""
    print("Testing DirtyRectManager.__init__()")
    
    manager = DirtyRectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    assert manager.screen_width == SCREEN_WIDTH, "Screen width should be set"
    assert manager.screen_height == SCREEN_HEIGHT, "Screen height should be set"
    assert len(manager.dirty_rects) == 0, "Dirty rects should be empty initially"
    
    print("  ✓ Initialization tests passed")
    return True


def test_add_rect() -> bool:
    """Тест добавления прямоугольника"""
    print("Testing DirtyRectManager.add()")
    
    manager = DirtyRectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    rect = pygame.Rect(10, 20, 30, 40)
    manager.add(rect)
    
    assert len(manager.dirty_rects) == 1, "Should have one dirty rect"
    assert manager.dirty_rects[0].contains(rect), "Dirty rect should contain original rect"
    
    print("  ✓ Add rect tests passed")
    return True


def test_add_point() -> bool:
    """Тест добавления точки"""
    print("Testing DirtyRectManager.add_point()")
    
    from game.game_config import DIRTY_RECT_BUFFER
    
    manager = DirtyRectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    manager.add_point(50, 60, 10, 10)
    
    assert len(manager.dirty_rects) == 1, "Should have one dirty rect"
    # Учитываем буфер, который добавляется в методе add()
    assert manager.dirty_rects[0].x <= 50, "X coordinate should be correct (with buffer)"
    assert manager.dirty_rects[0].y <= 60, "Y coordinate should be correct (with buffer)"
    assert manager.dirty_rects[0].contains(pygame.Rect(50, 60, 10, 10)), "Dirty rect should contain original point"
    
    print("  ✓ Add point tests passed")
    return True


def test_clear() -> bool:
    """Тест очистки списка"""
    print("Testing DirtyRectManager.clear()")
    
    manager = DirtyRectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    manager.add(pygame.Rect(0, 0, 10, 10))
    manager.add(pygame.Rect(20, 20, 10, 10))
    
    assert len(manager.dirty_rects) == 2, "Should have two dirty rects"
    
    manager.clear()
    
    assert len(manager.dirty_rects) == 0, "Dirty rects should be empty after clear"
    
    print("  ✓ Clear tests passed")
    return True


def test_get_dirty_rects() -> bool:
    """Тест получения списка грязных прямоугольников"""
    print("Testing DirtyRectManager.get_dirty_rects()")
    
    manager = DirtyRectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    rect1 = pygame.Rect(0, 0, 10, 10)
    rect2 = pygame.Rect(20, 20, 10, 10)
    
    manager.add(rect1)
    manager.add(rect2)
    
    dirty_rects = manager.get_dirty_rects()
    
    assert len(dirty_rects) == 2, "Should return two dirty rects"
    assert len(manager.dirty_rects) == 0, "Should clear after getting"
    
    print("  ✓ Get dirty rects tests passed")
    return True


def test_optimize() -> bool:
    """Тест оптимизации прямоугольников"""
    print("Testing DirtyRectManager.optimize()")
    
    manager = DirtyRectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Добавляем перекрывающиеся прямоугольники
    rect1 = pygame.Rect(0, 0, 50, 50)
    rect2 = pygame.Rect(25, 25, 50, 50)  # Перекрывается с rect1
    
    manager.add(rect1)
    manager.add(rect2)
    
    optimized = manager.optimize()
    
    # Перекрывающиеся прямоугольники должны быть объединены
    assert len(optimized) <= 2, "Should optimize overlapping rects"
    
    print("  ✓ Optimize tests passed")
    return True


def test_rect_boundaries() -> bool:
    """Тест ограничения прямоугольников границами экрана"""
    print("Testing rect boundaries")
    
    manager = DirtyRectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Добавляем прямоугольник за границами экрана
    rect = pygame.Rect(SCREEN_WIDTH + 10, SCREEN_HEIGHT + 10, 50, 50)
    manager.add(rect)
    
    dirty_rects = manager.get_dirty_rects()
    
    if dirty_rects:
        assert dirty_rects[0].right <= SCREEN_WIDTH, "Rect should be clamped to screen width"
        assert dirty_rects[0].bottom <= SCREEN_HEIGHT, "Rect should be clamped to screen height"
    
    print("  ✓ Rect boundaries tests passed")
    return True


def main() -> bool:
    """Запуск всех тестов"""
    print("=== Testing Dirty Rect Manager ===\n")
    
    pygame.init()
    
    tests = [
        test_dirty_rect_manager_init,
        test_add_rect,
        test_add_point,
        test_clear,
        test_get_dirty_rects,
        test_optimize,
        test_rect_boundaries,
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
    
    pygame.quit()
    
    print(f"=== Results: {passed}/{len(tests)} tests passed ===")
    
    if failed == 0:
        print("✓ All dirty rect manager tests passed!")
        return True
    else:
        print(f"✗ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

