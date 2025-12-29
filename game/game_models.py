"""
Модели данных для игры Арканоид.

Содержит классы Ball, Paddle и GameState, которые представляют
игровые объекты и состояние игры.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional

import pygame

from .game_config import (
    BALL_SIZE,
    BALL_SPEED_DEFAULT,
    PADDLE_HEIGHT,
    PADDLE_SPEED,
    PADDLE_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from .settings import SettingsManager

@dataclass
class Paddle:
    """Модель платформы (ракетки) игрока."""

    rect: pygame.Rect = field(
        default_factory=lambda: pygame.Rect(
            (SCREEN_WIDTH - PADDLE_WIDTH) // 2,
            SCREEN_HEIGHT - 60,
            PADDLE_WIDTH,
            PADDLE_HEIGHT,
        )
    )

    def move(self, direction: int) -> None:
        """
        Перемещает платформу в указанном направлении.
        
        Args:
            direction: -1 (влево) или 1 (вправо)
        """
        self.rect.x += direction * PADDLE_SPEED
        paddle_half_width: int = PADDLE_WIDTH // 2
        min_center_x: int = paddle_half_width
        max_center_x: int = SCREEN_WIDTH - paddle_half_width
        self.rect.centerx = max(min_center_x, min(max_center_x, self.rect.centerx))

@dataclass
class Ball:
    """Модель мяча с интегрированным управлением скоростью."""

    rect: pygame.Rect = field(
        default_factory=lambda: pygame.Rect(
            (SCREEN_WIDTH - BALL_SIZE) // 2,
            SCREEN_HEIGHT // 2,
            BALL_SIZE,
            BALL_SIZE,
        )
    )
    vel_x: int = field(
        default_factory=lambda: random.choice([-BALL_SPEED_DEFAULT, BALL_SPEED_DEFAULT])
    )
    vel_y: int = field(default_factory=lambda: -BALL_SPEED_DEFAULT)
    current_speed: int = field(default_factory=lambda: BALL_SPEED_DEFAULT)
    _last_vel_x: int = field(default=0)
    _just_bounced: bool = field(default=False)
    _bounce_frame: int = field(default=0)
    _wall_bounce_count: int = field(default=0)

    def update(self) -> None:
        """Обновляет позицию мяча и обрабатывает столкновения со стенами."""
        ball_radius: int = BALL_SIZE // 2
        min_center_x: int = ball_radius
        max_center_x: int = SCREEN_WIDTH - ball_radius
        min_center_y: int = ball_radius

        new_center_x: int = self.rect.centerx + self.vel_x
        new_center_y: int = self.rect.centery + self.vel_y

        # Проверяем столкновение со стенами по горизонтали
        if new_center_x < min_center_x:
            new_center_x = min_center_x
            self.vel_x *= -1
        elif new_center_x > max_center_x:
            new_center_x = max_center_x
            self.vel_x *= -1

        self.rect.centerx = new_center_x

        # Проверяем столкновение с потолком
        if new_center_y < min_center_y:
            new_center_y = min_center_y
            self.vel_y *= -1
            self._wall_bounce_count = 0
            # При столкновении корректируем позицию до границы
            self.rect.centery = min_center_y
        else:
            # Обновляем позицию только когда нет столкновения
            self.rect.centery = new_center_y

        # Защита от зацикливания у стен
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self._wall_bounce_count += 1

            if self._wall_bounce_count > 10:
                self.vel_y += random.choice([-1, 0, 1])
                self._wall_bounce_count = 0

    def bounce_vertical(self) -> None:
        """Отражает мяч по вертикали."""
        if self.vel_y == 0:
            self.vel_y = -self.current_speed
        else:
            self.vel_y *= -1

    def reset(self, paddle_rect: pygame.Rect) -> None:
        """Сбрасывает мяч на платформу с текущей скоростью."""
        ball_radius: int = BALL_SIZE // 2
        self.rect.centerx = paddle_rect.centerx
        self.rect.centery = paddle_rect.top - ball_radius - 5
        self.vel_x = random.choice([-self.current_speed, self.current_speed])
        self.vel_y = -self.current_speed

    def set_speed(
        self,
        speed: int,
        settings_manager: Optional[SettingsManager] = None,
    ) -> None:
        """
        Устанавливает скорость мяча и обновляет настройки.
        КРИТИЧНО: Сохраняет направление движения (угол траектории) при изменении скорости.
        """
        max_speed: int = 10
        if 1 <= speed <= max_speed:
            old_speed: int = self.current_speed
            self.current_speed = speed
            
            # КРИТИЧНО: Сохраняем направление движения (угол траектории)
            # Вычисляем текущую длину вектора скорости (модуль)
            current_speed_magnitude = ((self.vel_x ** 2) + (self.vel_y ** 2)) ** 0.5
            
            if current_speed_magnitude > 0:
                # Мяч движется - сохраняем направление, меняем только модуль скорости
                # Нормализуем вектор скорости (приводим к единичной длине)
                normalized_vel_x = self.vel_x / current_speed_magnitude
                normalized_vel_y = self.vel_y / current_speed_magnitude
                
                # Применяем новую скорость, сохраняя направление
                # Используем более точное вычисление для сохранения пропорций
                # Сначала вычисляем с плавающей точкой
                new_vel_x_float = normalized_vel_x * speed
                new_vel_y_float = normalized_vel_y * speed
                
                # Округляем до ближайшего целого
                new_vel_x = round(new_vel_x_float)
                new_vel_y = round(new_vel_y_float)
                
                # КРИТИЧНО: Гарантируем сохранение направления при малых скоростях
                # Если после округления одна из компонент стала 0, но должна быть ненулевой
                # Используем порог 0.1 для определения значимости компоненты
                if new_vel_x == 0 and abs(normalized_vel_x) > 0.1:
                    # Восстанавливаем минимальное значение с сохранением знака
                    new_vel_x = 1 if normalized_vel_x > 0 else -1
                if new_vel_y == 0 and abs(normalized_vel_y) > 0.1:
                    # Восстанавливаем минимальное значение с сохранением знака
                    new_vel_y = 1 if normalized_vel_y > 0 else -1
                
                # КРИТИЧНО: Проверяем, что обе компоненты не стали нулевыми одновременно
                if new_vel_x == 0 and new_vel_y == 0:
                    # Если обе компоненты нулевые, используем направление из нормализованного вектора
                    # Выбираем компоненту с большей абсолютной величиной
                    if abs(normalized_vel_x) > abs(normalized_vel_y):
                        new_vel_x = speed if normalized_vel_x > 0 else -speed
                        new_vel_y = round(normalized_vel_y * speed)
                        if new_vel_y == 0:
                            new_vel_y = 1 if normalized_vel_y > 0 else -1
                    else:
                        new_vel_x = round(normalized_vel_x * speed)
                        if new_vel_x == 0:
                            new_vel_x = 1 if normalized_vel_x > 0 else -1
                        new_vel_y = speed if normalized_vel_y > 0 else -speed
                
                # Применяем новые значения
                self.vel_x = new_vel_x
                self.vel_y = new_vel_y
                
                # КРИТИЧНО: Нормализуем результирующий вектор к заданной скорости
                # для точного сохранения направления и предотвращения искажений
                result_magnitude = ((self.vel_x ** 2) + (self.vel_y ** 2)) ** 0.5
                if result_magnitude > 0:
                    # Масштабируем к нужной скорости, сохраняя направление
                    scale_factor = speed / result_magnitude
                    self.vel_x = round(self.vel_x * scale_factor)
                    self.vel_y = round(self.vel_y * scale_factor)
                    
                    # Финальная проверка: гарантируем, что направление сохранено
                    if self.vel_x == 0 and abs(normalized_vel_x) > 0.1:
                        self.vel_x = 1 if normalized_vel_x > 0 else -1
                    if self.vel_y == 0 and abs(normalized_vel_y) > 0.1:
                        self.vel_y = 1 if normalized_vel_y > 0 else -1
            else:
                # Мяч неподвижен - используем значения по умолчанию
                self.vel_x = random.choice([-speed, speed])
                self.vel_y = -speed

            if settings_manager:
                settings_manager.set_ball_speed(speed)

    def increase_speed(
        self, settings_manager: Optional[SettingsManager] = None
    ) -> None:
        """Увеличивает скорость на 1 (максимум 10)."""
        max_speed: int = 10
        if self.current_speed < max_speed:
            self.set_speed(self.current_speed + 1, settings_manager)

    def decrease_speed(
        self, settings_manager: Optional[SettingsManager] = None
    ) -> None:
        """Уменьшает скорость на 1 (минимум 1)."""
        if self.current_speed > 1:
            self.set_speed(self.current_speed - 1, settings_manager)

    def get_speed(self) -> int:
        """Возвращает текущую скорость мяча."""
        return self.current_speed

@dataclass
class GameState:
    """Состояние игры, содержащее все игровые данные."""

    score: int = 0
    lives_left: int = 3
    game_started: bool = False
    game_over: bool = False
    bricks: List[pygame.Rect] = field(default_factory=list)
    game_start_time: float = 0.0

    def reset(self) -> None:
        """Сбрасывает состояние игры к начальным значениям."""
        self.score = 0
        self.lives_left = 3
        self.game_started = False
        self.game_over = False
        self.bricks = []
        self.game_start_time = 0.0
