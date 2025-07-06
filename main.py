"""
main.py - Buildozer를 위한 메인 엔트리 포인트
"""

try:
    # KivyMD 버전 시도
    from LOTTO_MOBILE import LottoMobileApp
    app = LottoMobileApp()
except ImportError:
    # KivyMD가 없으면 간단한 버전 사용
    from LOTTO_SIMPLE import SimpleLottoApp
    app = SimpleLottoApp()

if __name__ == '__main__':
    app.run()