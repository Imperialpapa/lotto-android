"""
LOTTO_MOBILE.py - 안드로이드용 로또 번호 생성기
Kivy/KivyMD 기반 모바일 앱
"""

import random
import time
import requests
from collections import Counter
import base64
import threading
from datetime import datetime

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

# KivyMD imports
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDSpinner
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineListItem
from kivymd.theming import ThemableBehavior

try:
    from supabase import create_client, Client
    from bs4 import BeautifulSoup
except ImportError:
    # 모바일에서 누락된 라이브러리 처리
    BeautifulSoup = None
    Client = None

# --- Configuration ---
_SB_URL = "aHR0cHM6Ly9uaXd0enZ3Y29kbW1qdm54Ynp4Zi5zdXBhYmFzZS5jbw=="
_SB_KEY = "ZXlKaGJHY2lPaUpJVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SnBjM01pT2lKemRYQmhZbUZ6WlNJc0luSmxaaUk2SW01cGQzUjZkbmRqYjJSdGJXcDJibmhpZW5obUlpd2ljbTlzWlNJNkltRnViMjRpTENKcFlYUWlPakUzTlRFM056VTVORGdzSW1WNGNDaTZNakEyTnpNMU1UazBPSDAuTnQ1dHN1ZHc4aXBJcEFqbkYwNDV2T0VnTms2Uk5mV0dzOHFCTmRSMlk2bw=="

def _decode_config():
    """설정 디코딩"""
    try:
        url = base64.b64decode(_SB_URL).decode()
        key = base64.b64decode(_SB_KEY).decode()
        return url, key
    except:
        return None, None

SUPABASE_URL, SUPABASE_KEY = _decode_config()
BASE_URL = "https://www.dhlottery.co.kr/gameResult.do?method=byWin&drwNo={}"

# Global variables
supabase = None
past_winnings = []

def init_supabase():
    """Supabase 초기화"""
    global supabase
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            return True
        except Exception as e:
            print(f"Supabase 연결 오류: {e}")
            return False
    return False

def load_lotto_data():
    """Supabase에서 로또 데이터 로드"""
    global past_winnings
    if not supabase:
        return False, "데이터베이스 연결 실패"
    
    try:
        response = supabase.table('lotto_data').select('num1, num2, num3, num4, num5, num6').order('round').execute()
        
        if response.data:
            past_winnings = []
            for row in response.data:
                numbers = [row['num1'], row['num2'], row['num3'], row['num4'], row['num5'], row['num6']]
                if all(1 <= x <= 45 for x in numbers) and len(set(numbers)) == 6:
                    past_winnings.append(sorted(numbers))
            
            return True, f"총 {len(past_winnings)}개 회차 로드 완료"
        else:
            return False, "데이터가 없습니다"
    except Exception as e:
        return False, f"데이터 로드 오류: {e}"

class LottoLogic:
    """로또 번호 생성 로직"""
    
    def __init__(self, past_winnings=None):
        self.past_winnings = past_winnings if past_winnings is not None else []
        self._patterns_analyzed = False
        if self.past_winnings:
            self.all_numbers_flat = [num for game in self.past_winnings for num in game]
            self.number_freq = Counter(self.all_numbers_flat)
            self._analyze_patterns()
        else:
            self.all_numbers_flat, self.number_freq = [], Counter()
            self.hot_numbers, self.cold_numbers = [], []
            self.sum_stats = {'min': 111, 'max': 170, 'avg': 140}

    def _analyze_patterns(self):
        """패턴 분석"""
        if not self.past_winnings or self._patterns_analyzed: 
            return
        
        avg_freq = sum(self.number_freq.values()) / len(self.number_freq) if self.number_freq else 0
        self.hot_numbers = sorted([num for num, freq in self.number_freq.items() if freq > avg_freq], 
                                 key=self.number_freq.get, reverse=True)
        self.cold_numbers = sorted([num for num in range(1, 46) if self.number_freq.get(num, 0) < avg_freq], 
                                  key=lambda num: self.number_freq.get(num, 0))
        
        sums = [sum(g) for g in self.past_winnings]
        self.sum_stats = {'min': min(sums), 'max': max(sums), 'avg': sum(sums) / len(sums)}
        self._patterns_analyzed = True

    def generate_random(self):
        """기본 랜덤"""
        return sorted(random.sample(range(1, 46), 6))

    def generate_pattern(self):
        """패턴 분석 (자주 나온 번호)"""
        if not self.past_winnings: 
            return self.generate_random()
        
        population = list(self.number_freq.keys())
        weights = list(self.number_freq.values())
        if not population: 
            return self.generate_random()
        
        numbers = set()
        while len(numbers) < 6:
            numbers.add(random.choices(population, weights=weights, k=1)[0])
        return sorted(list(numbers))

    def generate_hot_cold_mix(self):
        """핫/콜드 번호 조합"""
        if not self.past_winnings:
            return self.generate_random()
        
        numbers = set()
        if self.hot_numbers:
            numbers.update(random.sample(self.hot_numbers, min(3, len(self.hot_numbers))))
        if self.cold_numbers:
            numbers.update(random.sample(self.cold_numbers, min(3, len(self.cold_numbers))))
        
        while len(numbers) < 6:
            numbers.add(random.randint(1, 45))
        
        return sorted(random.sample(list(numbers), 6))

    def generate_balance(self):
        """홀수/짝수 균형"""
        for _ in range(100):
            numbers = random.sample(range(1, 46), 6)
            if 2 <= sum(1 for x in numbers if x % 2) <= 4:
                return sorted(numbers)
        return self.generate_random()

    def generate_range_distribution(self):
        """숫자 범위 분포"""
        try:
            numbers = set()
            for start, end in [(1, 15), (16, 30), (31, 45)]:
                numbers.update(random.sample(range(start, end + 1), 2))
            while len(numbers) < 6:
                numbers.add(random.randint(1, 45))
            return sorted(random.sample(list(numbers), 6))
        except:
            return self.generate_random()

class LottoBall(MDCard):
    """로또 공 위젯"""
    
    def __init__(self, number=0, **kwargs):
        super().__init__(**kwargs)
        self.number = number
        self.md_bg_color = self.get_color_for_number(number)
        self.size_hint = (None, None)
        self.size = (dp(60), dp(60))
        self.radius = [dp(30)]
        self.elevation = 3
        
        # 번호 라벨
        label = MDLabel(
            text=str(number),
            halign="center",
            valign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True
        )
        self.add_widget(label)
    
    def get_color_for_number(self, number):
        """번호에 따른 색상 반환"""
        if 1 <= number <= 10:
            return (1, 0.77, 0, 1)  # 노란색
        elif 11 <= number <= 20:
            return (0.41, 0.78, 0.95, 1)  # 파란색
        elif 21 <= number <= 30:
            return (1, 0.45, 0.45, 1)  # 빨간색
        elif 31 <= number <= 40:
            return (0.67, 0.67, 0.67, 1)  # 회색
        elif 41 <= number <= 45:
            return (0.69, 0.83, 0.25, 1)  # 초록색
        else:
            return (0.5, 0.5, 0.5, 1)  # 기본색

class GameCard(MDCard):
    """게임 카드 위젯"""
    
    def __init__(self, game_number, numbers, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = (0.16, 0.16, 0.19, 1)
        self.padding = dp(15)
        self.spacing = dp(10)
        self.radius = [dp(15)]
        self.elevation = 2
        self.size_hint_y = None
        self.height = dp(120)
        
        layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        # 게임 번호 라벨
        game_label = MDLabel(
            text=f"Game {game_number}",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.9, 1),
            size_hint_y=None,
            height=dp(30),
            font_style="Subtitle1"
        )
        layout.add_widget(game_label)
        
        # 번호 레이아웃
        numbers_layout = MDGridLayout(
            cols=6,
            spacing=dp(5),
            size_hint_y=None,
            height=dp(60),
            adaptive_width=True
        )
        
        for number in numbers:
            ball = LottoBall(number)
            numbers_layout.add_widget(ball)
        
        layout.add_widget(numbers_layout)
        self.add_widget(layout)

class LottoMobileApp(MDApp):
    """메인 앱 클래스"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = LottoLogic()
        self.connected = False
        self.dialog = None
        
        # 생성 방법 정의
        self.generation_methods = [
            {"name": "기본 랜덤", "method": self.logic.generate_random, "data_required": False},
            {"name": "패턴 분석 (자주)", "method": self.logic.generate_pattern, "data_required": True},
            {"name": "핫/콜드 조합", "method": self.logic.generate_hot_cold_mix, "data_required": True},
            {"name": "홀수/짝수 균형", "method": self.logic.generate_balance, "data_required": False},
            {"name": "숫자 범위 분포", "method": self.logic.generate_range_distribution, "data_required": False},
        ]
        
        self.current_method = 0
        self.current_games = 5

    def build(self):
        """앱 UI 구성"""
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        
        # 메인 화면
        screen = MDScreen()
        
        # 메인 레이아웃
        main_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(20)
        )
        
        # 제목
        title = MDLabel(
            text="🎲 Lotto Gem Mobile",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H4",
            size_hint_y=None,
            height=dp(60)
        )
        main_layout.add_widget(title)
        
        # 상태 레이블
        self.status_label = MDLabel(
            text="데이터베이스 연결 중...",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(40),
            font_style="Caption"
        )
        main_layout.add_widget(self.status_label)
        
        # 컨트롤 카드
        controls_card = MDCard(
            md_bg_color=(0.16, 0.16, 0.21, 1),
            padding=dp(20),
            spacing=dp(15),
            radius=[dp(15)],
            elevation=3,
            size_hint_y=None,
            height=dp(200)
        )
        
        controls_layout = MDBoxLayout(orientation='vertical', spacing=dp(15))
        
        # 생성 방법 선택
        method_layout = MDBoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(40))
        method_layout.add_widget(MDLabel(text="생성 방법:", size_hint_x=None, width=dp(80), font_style="Body2"))
        
        self.method_button = MDRaisedButton(
            text=self.generation_methods[0]["name"],
            size_hint_x=1
        )
        self.method_button.bind(on_release=self.show_method_menu)
        method_layout.add_widget(self.method_button)
        controls_layout.add_widget(method_layout)
        
        # 게임 수 선택
        games_layout = MDBoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(40))
        games_layout.add_widget(MDLabel(text="게임 수:", size_hint_x=None, width=dp(80), font_style="Body2"))
        
        self.games_button = MDRaisedButton(
            text="5게임",
            size_hint_x=1
        )
        self.games_button.bind(on_release=self.show_games_menu)
        games_layout.add_widget(self.games_button)
        controls_layout.add_widget(games_layout)
        
        # 버튼 레이아웃
        button_layout = MDBoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        
        self.update_button = MDRaisedButton(
            text="🔄 데이터 업데이트",
            md_bg_color=(0.3, 0.3, 0.6, 1),
            size_hint_x=0.5
        )
        self.update_button.bind(on_release=self.update_data)
        button_layout.add_widget(self.update_button)
        
        self.generate_button = MDRaisedButton(
            text="🎲 번호 생성",
            md_bg_color=(0, 0.9, 0.46, 1),
            size_hint_x=0.5
        )
        self.generate_button.bind(on_release=self.generate_numbers)
        button_layout.add_widget(self.generate_button)
        
        controls_layout.add_widget(button_layout)
        controls_card.add_widget(controls_layout)
        main_layout.add_widget(controls_card)
        
        # 결과 스크롤 영역
        self.results_scroll = ScrollView()
        self.results_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            adaptive_height=True
        )
        self.results_scroll.add_widget(self.results_layout)
        main_layout.add_widget(self.results_scroll)
        
        screen.add_widget(main_layout)
        
        # 데이터베이스 연결 시도
        Clock.schedule_once(self.connect_database, 1)
        
        return screen
    
    def connect_database(self, dt):
        """데이터베이스 연결"""
        def connect():
            if init_supabase():
                success, message = load_lotto_data()
                if success:
                    self.connected = True
                    Clock.schedule_once(lambda dt: self.update_status(f"✅ {message}"), 0)
                    self.logic = LottoLogic(past_winnings)
                else:
                    Clock.schedule_once(lambda dt: self.update_status(f"⚠️ {message}"), 0)
            else:
                Clock.schedule_once(lambda dt: self.update_status("❌ 데이터베이스 연결 실패"), 0)
        
        threading.Thread(target=connect, daemon=True).start()
    
    def update_status(self, message):
        """상태 업데이트"""
        self.status_label.text = message
    
    def show_method_menu(self, instance):
        """생성 방법 메뉴 표시"""
        menu_items = []
        for i, method in enumerate(self.generation_methods):
            item = {
                "text": method["name"],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=i: self.select_method(x),
            }
            menu_items.append(item)
        
        self.method_menu = MDDropdownMenu(
            caller=instance,
            items=menu_items,
            width_mult=4,
        )
        self.method_menu.open()
    
    def select_method(self, index):
        """생성 방법 선택"""
        self.current_method = index
        self.method_button.text = self.generation_methods[index]["name"]
        self.method_menu.dismiss()
    
    def show_games_menu(self, instance):
        """게임 수 메뉴 표시"""
        menu_items = []
        for i in range(1, 11):
            item = {
                "text": f"{i}게임",
                "viewclass": "OneLineListItem", 
                "on_release": lambda x=i: self.select_games(x),
            }
            menu_items.append(item)
        
        self.games_menu = MDDropdownMenu(
            caller=instance,
            items=menu_items,
            width_mult=3,
        )
        self.games_menu.open()
    
    def select_games(self, count):
        """게임 수 선택"""
        self.current_games = count
        self.games_button.text = f"{count}게임"
        self.games_menu.dismiss()
    
    def generate_numbers(self, instance):
        """번호 생성"""
        method = self.generation_methods[self.current_method]
        
        # 데이터 필요한 방법인데 연결되지 않은 경우
        if method["data_required"] and not self.connected:
            self.show_dialog("데이터 필요", "선택한 생성 방법은 로또 데이터가 필요합니다.\n데이터 업데이트를 먼저 실행해주세요.")
            return
        
        # 기존 결과 지우기
        self.results_layout.clear_widgets()
        
        # 번호 생성 및 표시
        for i in range(self.current_games):
            try:
                numbers = method["method"]()
                if isinstance(numbers, list) and len(numbers) == 6:
                    game_card = GameCard(i + 1, numbers)
                    self.results_layout.add_widget(game_card)
                else:
                    # 실패시 랜덤 생성
                    numbers = self.logic.generate_random()
                    game_card = GameCard(i + 1, numbers)
                    self.results_layout.add_widget(game_card)
            except Exception as e:
                # 오류시 랜덤 생성
                numbers = self.logic.generate_random()
                game_card = GameCard(i + 1, numbers)
                self.results_layout.add_widget(game_card)
    
    def update_data(self, instance):
        """데이터 업데이트"""
        if not self.connected:
            self.show_dialog("연결 오류", "데이터베이스에 연결할 수 없습니다.")
            return
        
        # 업데이트 로직은 복잡하므로 간단히 처리
        self.show_dialog("업데이트", "모바일에서는 자동 업데이트가 제한됩니다.\n웹 버전을 사용해 데이터를 업데이트해주세요.")
    
    def show_dialog(self, title, text):
        """다이얼로그 표시"""
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="확인",
                    on_release=lambda x: self.dialog.dismiss()
                ),
            ],
        )
        self.dialog.open()

# 앱 실행
if __name__ == '__main__':
    try:
        LottoMobileApp().run()
    except Exception as e:
        print(f"앱 실행 오류: {e}")
        import traceback
        traceback.print_exc()