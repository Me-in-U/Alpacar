#!/usr/bin/env python3
"""
웹 기반 마우스 구역 설정 도구
HTML5 Canvas를 사용한 마우스 인터페이스
"""

import base64
import json
import os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import cv2

def extract_frame_from_video(video_path, output_path=None):
    """비디오에서 첫 번째 프레임 추출"""
    if not os.path.exists(video_path):
        print(f"❌ 비디오 파일이 없습니다: {video_path}")
        return None
    
    if output_path is None:
        output_path = f"{os.path.splitext(video_path)[0]}_first_frame.jpg"
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"❌ 비디오를 열 수 없습니다: {video_path}")
            return None
        
        # 첫 번째 프레임 읽기
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print(f"❌ 비디오에서 프레임을 읽을 수 없습니다: {video_path}")
            return None
        
        # 이미지 저장
        success = cv2.imwrite(output_path, frame)
        
        if success:
            print(f"✅ 첫 번째 프레임 추출 완료: {output_path}")
            print(f"📐 이미지 크기: {frame.shape[1]}x{frame.shape[0]}")
            return output_path
        else:
            print(f"❌ 이미지 저장 실패: {output_path}")
            return None
            
    except Exception as e:
        print(f"❌ 프레임 추출 오류: {e}")
        return None

class WebZoneSelector:
    def __init__(self, image_path):
        self.image_path = image_path
        self.port = 8080
        
        # 구역 순서
        self.zone_order = ['A1', 'A2', 'A3', 'A4', 'A5', 
                          'B1', 'B2', 'B3', 
                          'C1', 'C2', 'C3']
        
    def create_html_interface(self):
        """HTML 인터페이스 생성"""
        
        # 이미지를 base64로 인코딩
        with open(self.image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>주차 구역 설정 도구</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f0f0f0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .canvas-container {{
            border: 2px solid #ddd;
            display: inline-block;
            position: relative;
            margin-bottom: 20px;
        }}
        canvas {{
            cursor: crosshair;
            display: block;
        }}
        .controls {{
            margin: 10px 0;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 5px;
        }}
        .zone-info {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        .current-zone {{
            color: #ff6600;
        }}
        .progress {{
            background: #e0e0e0;
            border-radius: 10px;
            padding: 3px;
            margin: 10px 0;
        }}
        .progress-bar {{
            background: #4CAF50;
            height: 20px;
            border-radius: 7px;
            transition: width 0.3s;
        }}
        .buttons {{
            margin: 10px 0;
        }}
        button {{
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn-primary {{ background: #007bff; color: white; }}
        .btn-warning {{ background: #ffc107; color: black; }}
        .btn-danger {{ background: #dc3545; color: white; }}
        .btn-success {{ background: #28a745; color: white; }}
        button:hover {{ opacity: 0.8; }}
        .instructions {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .point-list {{
            margin: 10px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
        }}
        .zone-colors {{
            display: flex;
            gap: 10px;
            margin: 10px 0;
        }}
        .color-legend {{
            padding: 5px 10px;
            border-radius: 3px;
            color: white;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 주차 구역 설정 도구</h1>
            <p>마우스로 클릭하여 주차 구역을 설정하세요</p>
        </div>
        
        <div class="instructions">
            <h3>📋 사용법</h3>
            <ul>
                <li><strong>좌클릭:</strong> 구역 꼭지점 선택 (4개 필요)</li>
                <li><strong>우클릭:</strong> 마지막 점 제거</li>
                <li><strong>순서:</strong> A1→A2→A3→A4→A5→B1→B2→B3→C1→C2→C3</li>
                <li><strong>방향:</strong> 각 구역의 4개 점을 시계방향으로 클릭</li>
            </ul>
        </div>
        
        <div class="zone-colors">
            <div class="color-legend" style="background: #ff0000;">A구역 (빨강)</div>
            <div class="color-legend" style="background: #00ff00;">B구역 (초록)</div>
            <div class="color-legend" style="background: #0000ff;">C구역 (파랑)</div>
        </div>
        
        <div class="controls">
            <div class="zone-info">
                현재 구역: <span class="current-zone" id="currentZone">A1</span> 
                (<span id="progress">1/11</span>)
            </div>
            <div class="progress">
                <div class="progress-bar" id="progressBar" style="width: 9%"></div>
            </div>
            <div class="point-list" id="pointList">
                선택된 점: 0/4
            </div>
        </div>
        
        <div class="canvas-container">
            <canvas id="zoneCanvas" width="1656" height="1044"></canvas>
        </div>
        
        <div class="buttons">
            <button class="btn-warning" onclick="undoLastPoint()">↶ 마지막 점 제거</button>
            <button class="btn-danger" onclick="resetCurrentZone()">🔄 현재 구역 다시</button>
            <button class="btn-success" onclick="saveZones()">💾 저장</button>
            <button class="btn-primary" onclick="downloadResult()">📥 결과 다운로드</button>
        </div>
        
        <div id="output" style="margin-top: 20px;"></div>
    </div>

    <script>
        // 전역 변수
        const canvas = document.getElementById('zoneCanvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        
        const zoneOrder = ['A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3'];
        const zoneColors = {{
            'A1': '#ff0000', 'A2': '#ff0000', 'A3': '#ff0000', 'A4': '#ff0000', 'A5': '#ff0000',
            'B1': '#00ff00', 'B2': '#00ff00', 'B3': '#00ff00',
            'C1': '#0000ff', 'C2': '#0000ff', 'C3': '#0000ff'
        }};
        
        let currentZoneIndex = 0;
        let zones = {{}};
        let currentPoints = [];
        
        // 이미지 로드
        img.onload = function() {{
            // 캔버스 크기 조정 (화면에 맞게)
            const maxWidth = window.innerWidth - 100;
            const maxHeight = window.innerHeight - 400;
            
            let displayWidth = img.width;
            let displayHeight = img.height;
            
            if (displayWidth > maxWidth) {{
                displayHeight = (displayHeight * maxWidth) / displayWidth;
                displayWidth = maxWidth;
            }}
            
            if (displayHeight > maxHeight) {{
                displayWidth = (displayWidth * maxHeight) / displayHeight;
                displayHeight = maxHeight;
            }}
            
            canvas.width = displayWidth;
            canvas.height = displayHeight;
            canvas.style.width = displayWidth + 'px';
            canvas.style.height = displayHeight + 'px';
            
            redraw();
        }};
        
        img.src = 'data:image/jpeg;base64,{image_data}';
        
        // 마우스 이벤트
        canvas.addEventListener('click', function(e) {{
            if (currentZoneIndex >= zoneOrder.length) return;
            
            const rect = canvas.getBoundingClientRect();
            const scaleX = img.width / canvas.width;
            const scaleY = img.height / canvas.height;
            
            const x = Math.round((e.clientX - rect.left) * scaleX);
            const y = Math.round((e.clientY - rect.top) * scaleY);
            
            currentPoints.push([x, y]);
            console.log(`점 추가: (${{x}}, ${{y}})`);
            
            if (currentPoints.length === 4) {{
                // 구역 완성
                const zoneName = zoneOrder[currentZoneIndex];
                zones[zoneName] = [...currentPoints];
                currentPoints = [];
                currentZoneIndex++;
                
                console.log(`${{zoneName}} 구역 완성!`);
            }}
            
            updateUI();
            redraw();
        }});
        
        canvas.addEventListener('contextmenu', function(e) {{
            e.preventDefault();
            undoLastPoint();
        }});
        
        // 그리기 함수
        function redraw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // 이미지 그리기
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            
            const scaleX = canvas.width / img.width;
            const scaleY = canvas.height / img.height;
            
            // 완성된 구역들 그리기
            for (const [zoneName, points] of Object.entries(zones)) {{
                const color = zoneColors[zoneName];
                
                // 반투명 채우기
                ctx.globalAlpha = 0.3;
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.moveTo(points[0][0] * scaleX, points[0][1] * scaleY);
                for (let i = 1; i < points.length; i++) {{
                    ctx.lineTo(points[i][0] * scaleX, points[i][1] * scaleY);
                }}
                ctx.closePath();
                ctx.fill();
                
                // 경계선
                ctx.globalAlpha = 1.0;
                ctx.strokeStyle = color;
                ctx.lineWidth = 2;
                ctx.stroke();
                
                // 구역 이름
                const centerX = points.reduce((sum, p) => sum + p[0], 0) / points.length * scaleX;
                const centerY = points.reduce((sum, p) => sum + p[1], 0) / points.length * scaleY;
                
                ctx.fillStyle = 'white';
                ctx.font = 'bold 16px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(zoneName, centerX, centerY);
            }}
            
            // 현재 그리고 있는 점들
            if (currentPoints.length > 0 && currentZoneIndex < zoneOrder.length) {{
                const color = zoneColors[zoneOrder[currentZoneIndex]];
                
                // 점들 그리기
                ctx.fillStyle = '#ffff00';
                for (let i = 0; i < currentPoints.length; i++) {{
                    const x = currentPoints[i][0] * scaleX;
                    const y = currentPoints[i][1] * scaleY;
                    
                    ctx.beginPath();
                    ctx.arc(x, y, 5, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    // 점 번호
                    ctx.fillStyle = 'black';
                    ctx.font = 'bold 12px Arial';
                    ctx.fillText(i + 1, x + 10, y - 10);
                    ctx.fillStyle = '#ffff00';
                }}
                
                // 선 그리기
                if (currentPoints.length > 1) {{
                    ctx.strokeStyle = '#ffff00';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(currentPoints[0][0] * scaleX, currentPoints[0][1] * scaleY);
                    for (let i = 1; i < currentPoints.length; i++) {{
                        ctx.lineTo(currentPoints[i][0] * scaleX, currentPoints[i][1] * scaleY);
                    }}
                    ctx.stroke();
                }}
            }}
        }}
        
        // UI 업데이트
        function updateUI() {{
            const currentZoneName = currentZoneIndex < zoneOrder.length ? zoneOrder[currentZoneIndex] : '완료';
            const progress = `${{currentZoneIndex + 1}}/${{zoneOrder.length}}`;
            const progressPercent = ((currentZoneIndex + currentPoints.length / 4) / zoneOrder.length) * 100;
            
            document.getElementById('currentZone').textContent = currentZoneName;
            document.getElementById('progress').textContent = progress;
            document.getElementById('progressBar').style.width = progressPercent + '%';
            document.getElementById('pointList').innerHTML = 
                `선택된 점: ${{currentPoints.length}}/4<br>` +
                currentPoints.map((p, i) => `점 ${{i+1}}: (${{p[0]}}, ${{p[1]}})`).join('<br>');
        }}
        
        // 기능 함수들
        function undoLastPoint() {{
            if (currentPoints.length > 0) {{
                currentPoints.pop();
                updateUI();
                redraw();
            }}
        }}
        
        function resetCurrentZone() {{
            currentPoints = [];
            updateUI();
            redraw();
        }}
        
        function saveZones() {{
            const result = {{
                image_info: {{
                    width: img.width,
                    height: img.height,
                    source: 'angle_first_frame.jpg'
                }},
                zones: []
            }};
            
            for (const zoneName of zoneOrder) {{
                if (zones[zoneName]) {{
                    const points = zones[zoneName];
                    const x_coords = points.map(p => p[0]);
                    const y_coords = points.map(p => p[1]);
                    
                    result.zones.push({{
                        name: zoneName,
                        points_absolute: points,
                        points_normalized: points.map(p => [
                            Math.round(p[0] / img.width * 10000) / 10000,
                            Math.round(p[1] / img.height * 10000) / 10000
                        ]),
                        bbox_normalized: {{
                            x1: Math.round(Math.min(...x_coords) / img.width * 10000) / 10000,
                            y1: Math.round(Math.min(...y_coords) / img.height * 10000) / 10000,
                            x2: Math.round(Math.max(...x_coords) / img.width * 10000) / 10000,
                            y2: Math.round(Math.max(...y_coords) / img.height * 10000) / 10000
                        }}
                    }});
                }}
            }}
            
            // Python 코드 생성
            let pythonCode = 'PARKING_ZONES_NORM = [\\n';
            for (const zone of result.zones) {{
                const bbox = zone.bbox_normalized;
                pythonCode += `    [${{bbox.x1}}, ${{bbox.y1}}, ${{bbox.x2}}, ${{bbox.y2}}],  # ${{zone.name}}\\n`;
            }}
            pythonCode += ']';
            
            document.getElementById('output').innerHTML = `
                <h3>💾 저장 결과</h3>
                <p>총 ${{Object.keys(zones).length}}개 구역 저장됨</p>
                <h4>Python 코드:</h4>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto;">${{pythonCode}}</pre>
                <h4>JSON 데이터:</h4>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; max-height: 300px; overflow-y: auto;">${{JSON.stringify(result, null, 2)}}</pre>
            `;
            
            // 서버로 전송
            fetch('/save', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(result)
            }}).then(response => response.text())
              .then(data => console.log('저장 완료:', data));
        }}
        
        function downloadResult() {{
            const result = {{
                zones: zones,
                image_info: {{width: img.width, height: img.height}}
            }};
            
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", "parking_zones.json");
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        }}
        
        // 초기 UI 업데이트
        updateUI();
    </script>
</body>
</html>
        """
        
        return html_content
    
    def start_server(self):
        """웹 서버 시작"""
        
        class ZoneHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    html_content = self.server.zone_selector.create_html_interface()
                    self.wfile.write(html_content.encode())
                else:
                    super().do_GET()
            
            def do_POST(self):
                if self.path == '/save':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    try:
                        zone_data = json.loads(post_data.decode())
                        
                        # JSON 파일로 저장
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"parking_zones_web_{timestamp}.json"
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(zone_data, f, indent=2, ensure_ascii=False)
                        
                        # Python 코드도 저장
                        python_code = "PARKING_ZONES_NORM = [\\n"
                        for zone in zone_data['zones']:
                            bbox = zone['bbox_normalized']
                            python_code += f"    [{bbox['x1']}, {bbox['y1']}, {bbox['x2']}, {bbox['y2']}],  # {zone['name']}\\n"
                        python_code += "]"
                        
                        with open(f"parking_zones_web_{timestamp}.py", 'w', encoding='utf-8') as f:
                            f.write(python_code)
                        
                        print(f"✅ 웹에서 구역 저장 완료: {filename}")
                        print(f"📊 총 {len(zone_data['zones'])}개 구역")
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(f"저장 완료: {filename}".encode())
                        
                    except Exception as e:
                        print(f"❌ 저장 오류: {e}")
                        self.send_response(500)
                        self.end_headers()
        
        # 서버 설정
        server = HTTPServer(('localhost', self.port), ZoneHandler)
        server.zone_selector = self
        
        print(f"🌐 웹 구역 설정 도구 시작")
        print(f"📍 주소: http://localhost:{self.port}")
        print(f"💡 위 주소를 웹브라우저에서 열어서 마우스로 구역을 설정하세요!")
        print(f"🛑 종료하려면 Ctrl+C를 누르세요")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\\n👋 웹 서버를 종료합니다.")
            server.shutdown()


def main():
    image_path = "new_first_frame.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일이 없습니다: {image_path}")
        print("new.mp4에서 첫 번째 프레임을 추출해보겠습니다...")
        
        # new.mp4에서 첫 번째 프레임 추출 시도
        extracted_image = extract_frame_from_video("new.mp4", image_path)
        if not extracted_image:
            print("❌ 프레임 추출에 실패했습니다.")
            return
    
    selector = WebZoneSelector(image_path)
    selector.start_server()


if __name__ == "__main__":
    main()
