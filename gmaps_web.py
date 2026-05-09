from flask import Flask, render_template_string, request, jsonify, send_file
import requests
import csv
import os
import time
from datetime import datetime

API_KEY = "AIzaSyAfh1bFMqAj5-kfivLXLeMirU5D2nqMSjg"
PLACES_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GMaps Müşteri Bulucu</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #1a1a2e; color: #fff; min-height: 100vh; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; }
        h1 { text-align: center; color: #00d4ff; margin-bottom: 30px; font-size: 24px; }
        .card { background: #16213e; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #aaa; font-size: 14px; }
        input { width: 100%; padding: 15px; border: none; border-radius: 10px; background: #0f3460; color: #fff; font-size: 16px; margin-bottom: 15px; }
        input:focus { outline: 2px solid #00d4ff; }
        .btn { width: 100%; padding: 18px; background: #00d4ff; color: #1a1a2e; border: none; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .btn:disabled { background: #555; cursor: not-allowed; }
        .btn:hover:not(:disabled) { background: #00b8e6; }
        #status { margin-top: 20px; padding: 15px; border-radius: 10px; background: #0f3460; max-height: 300px; overflow-y: auto; font-size: 14px; line-height: 1.6; }
        .loading { display: none; text-align: center; margin-top: 10px; }
        .loading span { animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .result-item { padding: 10px 0; border-bottom: 1px solid #0f3460; }
        .result-item:last-child { border-bottom: none; }
        .result-name { font-weight: bold; color: #00d4ff; }
        .result-detail { color: #888; font-size: 12px; margin-top: 3px; }
        .download-links { margin-top: 20px; }
        .download-btn { display: inline-block; padding: 12px 20px; background: #e94560; color: #fff; text-decoration: none; border-radius: 8px; margin: 5px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🗺️ GMaps Müşteri Bulucu</h1>
        
        <div class="card">
            <label>Sektör / İş Kolu</label>
            <input type="text" id="sektor" placeholder="örn: restaurant, eczane, avukat">
            
            <label>Şehir</label>
            <input type="text" id="sehir" placeholder="örn: İstanbul">
            
            <label>İlçe (opsiyonel)</label>
            <input type="text" id="ilce" placeholder="örn: Kadıköy">
            
            <label>Maksimum Sonuç</label>
            <input type="number" id="max_sonuc" value="60" min="10" max="200">
            
            <button class="btn" id="araBtn" onclick="ara()">🔍 ARA</button>
            
            <div class="loading" id="loading">
                <span>🔄 Aranıyor...</span>
            </div>
        </div>
        
        <div id="status"></div>
        
        <div class="download-links" id="downloadLinks" style="display:none;">
            <a class="download-btn" href="/download/customers">📋 Tüm Verileri İndir</a>
            <a class="download-btn" href="/download/websites">🌐 Web Sitelerini İndir</a>
        </div>
    </div>
    
    <script>
        let isSearching = false;
        
        async function ara() {
            if (isSearching) return;
            
            const sektor = document.getElementById('sektor').value.trim();
            const sehir = document.getElementById('sehir').value.trim();
            const ilce = document.getElementById('ilce').value.trim();
            const max_sonuc = document.getElementById('max_sonuc').value;
            
            if (!sektor || !sehir) {
                alert('Sektör ve şehir giriniz!');
                return;
            }
            
            isSearching = true;
            document.getElementById('araBtn').disabled = true;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('status').innerHTML = '';
            document.getElementById('downloadLinks').style.display = 'none';
            
            try {
                const response = await fetch('/api/ara', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sektor, sehir, ilce, max_sonuc: parseInt(max_sonuc) })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let html = `<strong>✅ ${data.count} işletme bulundu!</strong><br><br>`;
                    data.results.forEach((r, i) => {
                        html += `<div class="result-item">
                            <div class="result-name">${i+1}. ${r.name}</div>
                            <div class="result-detail">⭐ ${r.rating} (${r.reviews} yorum)</div>
                            <div class="result-detail">📍 ${r.address}</div>
                            <div class="result-detail">📞 ${r.phone}</div>
                            <div class="result-detail">🌐 ${r.website}</div>
                        </div>`;
                    });
                    document.getElementById('status').innerHTML = html;
                    document.getElementById('downloadLinks').style.display = 'block';
                } else {
                    document.getElementById('status').innerHTML = `<span style="color:#e94560;">❌ Hata: ${data.error}</span>`;
                }
            } catch (e) {
                document.getElementById('status').innerHTML = `<span style="color:#e94560;">❌ Bağlantı hatası: ${e.message}</span>`;
            }
            
            isSearching = false;
            document.getElementById('araBtn').disabled = false;
            document.getElementById('loading').style.display = 'none';
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/ara", methods=["POST"])
def api_ara():
    data = request.json
    sektor = data.get("sektor", "").strip()
    sehir = data.get("sehir", "").strip()
    ilce = data.get("ilce", "").strip()
    max_results = data.get("max_sonuc", 60)
    
    if not sektor or not sehir:
        return jsonify({"success": False, "error": "Sektör ve şehir gerekli"})
    
    konum = f"{ilce}, {sehir}" if ilce else sehir
    
    all_places = []
    next_page_token = None
    
    while len(all_places) < max_results:
        params = {"query": f"{sektor} in {konum}", "key": API_KEY}
        if next_page_token:
            params["pagetoken"] = next_page_token
        
        try:
            response = requests.get(PLACES_URL, params=params)
            result_data = response.json()
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
        
        if "results" in result_data:
            all_places.extend(result_data["results"])
        
        next_page_token = result_data.get("next_page_token")
        if not next_page_token:
            break
        time.sleep(2)
    
    results = []
    for place in all_places[:max_results]:
        results.append({
            "name": place.get("name", "N/A"),
            "rating": place.get("rating", "N/A"),
            "reviews": place.get("user_ratings_total", "N/A"),
            "address": place.get("formatted_address", "N/A"),
            "phone": place.get("formatted_phone_number", "N/A"),
            "website": place.get("website", "N/A"),
            "query": sektor,
            "location": konum
        })
    
    save_path = os.path.dirname(os.path.abspath(__file__))
    
    csv_path = os.path.join(save_path, "customers.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "rating", "reviews", "address", "phone", "website", "query", "location"])
        writer.writeheader()
        writer.writerows(results)
    
    web_path = os.path.join(save_path, "websites_only.csv")
    with open(web_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "website"])
        for r in results:
            if r["website"] and r["website"] != "N/A":
                writer.writerow([r["name"], r["website"]])
    
    return jsonify({"success": True, "count": len(results), "results": results})

@app.route("/download/<filetype>")
def download(filetype):
    save_path = os.path.dirname(os.path.abspath(__file__))
    if filetype == "customers":
        return send_file(os.path.join(save_path, "customers.csv"), as_attachment=True)
    elif filetype == "websites":
        return send_file(os.path.join(save_path, "websites_only.csv"), as_attachment=True)
    return "Not found", 404

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Sunucu başlatıldı!")
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"📱 iPhone'dan erişim: http://{local_ip}:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)