# IoT_TermProject
Raspberry Pi, AWS, 초음파센서, 부저스피커를 이용한 경보음장치

![image](https://user-images.githubusercontent.com/65848753/131083265-11e23c9e-17c2-4411-8650-1bd563d3ed61.png)

동작원리
 - 1초 간격으로 초음파센서로 거리를 측정, 화면 상에 츨력
 - 측정된 거리가 10cm미만일 경우, 누군가 접근했다고 판단, 1초간 부저스피커에서 경보음을 출력
 - AWS의 SNS를 이용하여 등록된 이메일로 '누군가 접근했습니다.'라는 메시지를 전송
