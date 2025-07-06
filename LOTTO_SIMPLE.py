"""
LOTTO_SIMPLE.py - KivyMD 없이 기본 Kivy만 사용하는 간단한 버전
"""

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
import random

class LottoBall(Widget):
    def __init__(self, number=0, **kwargs):
        super().__init__(**kwargs)
        self.number = number
        self.size_hint = (None, None)
        self.size = (60, 60)
        
        with self.canvas:
            # 번호별 색상 설정
            if number <= 10:
                Color(1, 0.84, 0)  # 금색
            elif number <= 20:
                Color(0.2, 0.6, 1)  # 파란색
            elif number <= 30:
                Color(1, 0.2, 0.2)  # 빨간색
            elif number <= 40:
                Color(0.5, 0.5, 0.5)  # 회색
            else:
                Color(0.4, 0.8, 0.2)  # 초록색
            
            self.circle = Ellipse(pos=self.pos, size=self.size)
        
        # 번호 텍스트
        self.label = Label(
            text=str(number),
            color=(1, 1, 1, 1),
            font_size=20,
            pos=self.pos,
            size=self.size
        )
        self.add_widget(self.label)
        
        self.bind(pos=self.update_graphics)
        
    def update_graphics(self, *args):
        self.circle.pos = self.pos
        self.label.pos = self.pos

class SimpleLottoApp(App):
    def build(self):
        self.title = "Simple Lotto Generator"
        
        # 메인 레이아웃
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # 제목
        title = Label(
            text='🎲 Simple Lotto Generator',
            font_size=24,
            size_hint_y=None,
            height=50
        )
        main_layout.add_widget(title)
        
        # 컨트롤 영역
        control_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        # 생성 방법 선택
        method_label = Label(text='Method:', size_hint_x=None, width=80)
        self.method_spinner = Spinner(
            text='Random',
            values=['Random', 'Balanced', 'Range'],
            size_hint_x=None,
            width=120
        )
        
        # 게임 수 선택
        games_label = Label(text='Games:', size_hint_x=None, width=80)
        self.games_spinner = Spinner(
            text='5',
            values=['1', '2', '3', '5', '7', '10'],
            size_hint_x=None,
            width=80
        )
        
        # 생성 버튼
        generate_btn = Button(
            text='Generate Numbers',
            size_hint_x=None,
            width=150
        )
        generate_btn.bind(on_press=self.generate_numbers)
        
        control_layout.add_widget(method_label)
        control_layout.add_widget(self.method_spinner)
        control_layout.add_widget(Widget())  # 스페이서
        control_layout.add_widget(games_label)
        control_layout.add_widget(self.games_spinner)
        control_layout.add_widget(Widget())  # 스페이서
        control_layout.add_widget(generate_btn)
        
        main_layout.add_widget(control_layout)
        
        # 결과 영역
        self.results_layout = BoxLayout(orientation='vertical', spacing=10)
        main_layout.add_widget(self.results_layout)
        
        return main_layout
    
    def generate_random(self):
        """기본 랜덤 생성"""
        numbers = []
        while len(numbers) < 6:
            num = random.randint(1, 45)
            if num not in numbers:
                numbers.append(num)
        return sorted(numbers)
    
    def generate_balanced(self):
        """홀수/짝수 균형 맞춘 생성"""
        attempts = 0
        while attempts < 100:
            numbers = self.generate_random()
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            if 2 <= odd_count <= 4:
                return numbers
            attempts += 1
        return self.generate_random()
    
    def generate_range(self):
        """구간별 분포 생성"""
        numbers = []
        ranges = [(1, 15), (16, 30), (31, 45)]
        
        for start, end in ranges:
            count = 0
            while count < 2 and len(numbers) < 6:
                num = random.randint(start, end)
                if num not in numbers:
                    numbers.append(num)
                    count += 1
        
        return sorted(numbers)
    
    def generate_numbers(self, instance):
        """번호 생성 메인 함수"""
        method = self.method_spinner.text
        game_count = int(self.games_spinner.text)
        
        # 기존 결과 지우기
        self.results_layout.clear_widgets()
        
        # 결과 생성
        for i in range(game_count):
            if method == 'Balanced':
                numbers = self.generate_balanced()
            elif method == 'Range':
                numbers = self.generate_range()
            else:
                numbers = self.generate_random()
            
            # 게임 카드 생성
            game_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=100, spacing=5)
            
            # 게임 제목
            game_title = Label(
                text=f'Game {i+1}',
                size_hint_y=None,
                height=30,
                font_size=16
            )
            game_layout.add_widget(game_title)
            
            # 번호 공들
            balls_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=5)
            
            for number in numbers:
                ball = LottoBall(number=number)
                balls_layout.add_widget(ball)
            
            game_layout.add_widget(balls_layout)
            self.results_layout.add_widget(game_layout)

if __name__ == '__main__':
    SimpleLottoApp().run()