# 파이썬 자동 실행 서비스 업데이트

1. 서비스 파일 복사

   - sudo cp /home/ssafy/Documents/Test/autorun.service /etc/systemd/system/autorun.service

2. systemd 데몬 리로드

   - sudo systemctl daemon-reload

3. 부팅 시 자동실행 활성화

   - sudo systemctl enable autorun.service

4. 서비스 바로 시작

   - sudo systemctl start autorun.service

5. 서비스 상태 확인

   - sudo systemctl status autorun.service

6. 실시간 로그 보기

   - sudo journalctl -u autorun.service -f

7. 재부팅 후 자동실행 테스트

   - sudo reboot
