from flask import Flask, render_template, request, jsonify
from facebook_uploader.uploader import FacebookReelsAPI
from facebook_uploader.reel import Reel
import requests
import os
import time
from datetime import datetime
from pytz import timezone

app = Flask(__name__)

# Ganti dengan akses token asli Anda
USER_ACCESS_TOKEN = "YOUR_ACCES_TOKEN"


def get_page_list(user_access_token):
    """
    Mengambil daftar halaman berdasarkan user access token.
    """
    url = f"https://graph.facebook.com/v16.0/me/accounts?access_token={user_access_token}"
    response = requests.get(url)
    if response.status_code == 200:
        pages = response.json().get("data", [])
        return pages
    else:
        return []


@app.route('/')
def index():
    """
    Halaman utama dengan form upload video.
    """
    pages = get_page_list(USER_ACCESS_TOKEN)
    return render_template('index.html', pages=pages)


@app.route('/upload', methods=['POST'])
def upload_reels():
    """
    Endpoint untuk mengunggah banyak video reels.
    """
    try:
        # Data dari form
        selected_pages = request.form.getlist('pages')  # List halaman yang dipilih
        descriptions = request.form.getlist('description[]')  # List deskripsi
        schedule_times = request.form.getlist('schedule_time[]')  # List waktu jadwal
        videos = request.files.getlist('video[]')  # List video

        # Validasi jumlah data
        if len(descriptions) != len(videos) or len(schedule_times) != len(videos):
            return jsonify({"status": "error", "message": "Jumlah data tidak konsisten."})

        # Loop melalui semua video yang diunggah
        for i, video in enumerate(videos):
            # Simpan file sementara
            file_path = f"temp_{int(time.time())}_{i}.mp4"
            video.save(file_path)

            # Parsing waktu jadwal
            schedule_time = schedule_times[i]
            if schedule_time:
                local_time = datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M')
                jakarta_tz = timezone('Asia/Jakarta')
                local_time = jakarta_tz.localize(local_time)

                # Konversi ke UTC
                utc_time = local_time.astimezone(timezone('UTC'))
                publish_time = utc_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                publish_time = None

            # Upload ke semua halaman
            for page in selected_pages:
                page_id, page_access_token = page.split('|')  # Pisahkan ID dan token
                reels_api = FacebookReelsAPI(page_id, page_access_token)
                reel = Reel(description=descriptions[i], file_path=file_path)

                # Upload video
                reels_api.upload(reel, publish_time)

            # Hapus file sementara
            os.remove(file_path)

        return jsonify({"status": "success", "message": "Semua video berhasil diupload ke halaman yang dipilih!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
