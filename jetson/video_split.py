from moviepy import VideoFileClip
import math
import os

# 입력 파일 경로
input_path = "WIN_20250808_17_40_04_Pro.mp4"

# 출력 폴더 설정
output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

# 비디오 로드
video = VideoFileClip(input_path)
duration = video.duration

# 30초 단위로 자르기
output_files = []
split_seconds = 30

print(f"비디오 전체 길이: {duration:.2f}초")
print(f"{split_seconds}초 단위로 분할합니다.")

for idx, start_time in enumerate(range(0, math.ceil(duration), split_seconds), 1):
    end_time = min(start_time + split_seconds, duration)
    print(f"구간 {idx}: {start_time}초 ~ {end_time}초")
    subclip = video.subclipped(start_time, end_time)

    output_filename = os.path.join(output_dir, f"video_part_{idx}.mp4")
    subclip.write_videofile(output_filename, codec="libx264", audio_codec="aac", logger=None)
    output_files.append(output_filename)

video.close()

print("분할된 파일 목록:")
for f in output_files:
    print(f)

# 필요시 리스트 반환
# output_files
