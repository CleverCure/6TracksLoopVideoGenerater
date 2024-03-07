from flask import Flask, render_template, request, redirect, url_for, flash
import magic
from moviepy.editor import *
from moviepy.video.fx.resize import resize
import os
import math
import random
import secrets
import sqlite3
import time
import secrets
import string

# number of items to show
num_items = 10

dbname = 'database.db'
conn = sqlite3.connect(dbname)
cur = conn.cursor()

query = """
    CREATE TABLE IF NOT EXISTS videos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_title TEXT NOT NULL,
        video_name TEXT NOT NULL,
        created_at INTEGER NOT NULL
    )
"""
cur.execute(query)

# insert test data
# query = "INSERT INTO videos(video_title, video_name, created_at) values(test data, test data, 1234567890)"
# cur.execute(query)

conn.commit()
conn.close()


def random_string(length):
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))


def has_data(table_name, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]

    conn.close()

    return count > 0

def table_exists(table_name, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    result = cursor.fetchone()
    conn.close()
    return result is None

UPLOAD_FOLDER = "tmp"
ALLOWED_EXTENSIONS = {"mp4"}

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


ALLOWED_PATHS = ["/", "/results", "/list"]
@app.before_request
def check_referer():
    if request.path not in ALLOWED_PATHS and request.referrer is None:
        return redirect(url_for("index"))


@app.route("/")
def index():


    data_exists = 1

    if table_exists('videos', dbname) or not has_data('videos', dbname):
        data_exists = 0

    return render_template("index.html", data_exists=data_exists)


@app.route("/post", methods=["POST"])
def post():
    loop_type = request.form["type"]
    file = request.files["file"]
    video_title = request.form["video_title"]
    created_at = math.floor(time.time())
    video_name = random_string(8) + str(created_at)

    # mime type
    file_type = magic.from_buffer(file.read(), mime=True)

    # log
    app.logger.info("File type: %s", file_type)

    if file_type != "video/mp4" and file_type != "video/quicktime":
        flash('MP4ファイルを選択してください')
        return redirect(url_for("error"))


    if file_type == "video/quicktime" or file_type == "video/mp4":
        file.seek(0, os.SEEK_END)
        app.logger.info(file.tell())
        file.seek(0, 0)

        if file_type == "video/quicktime":
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], video_name + ".mov"))
            clip = VideoFileClip(f"tmp/{video_name}.mov")
        else:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], video_name + ".mp4"))
            clip = VideoFileClip(f"tmp/{video_name}.mp4")

        clip = clip.volumex(0.6)

        if clip.duration > 300 or clip.duration < 40:
            flash('40秒以上 5分以下の動画をアップロードしてください')
            return redirect(url_for("error"))


        ############################
        # config

        # reduction rate
        r_rate = 2

        # background color
        rgb_color = [
            [255, 255, 0],
            [4, 255, 255],
            [0, 246, 2],
            [255, 30, 255],
            [255, 49, 0],
            [0, 0, 251]
        ]

        start_time = [1/2, 5/6, 1/6, 3/5, 1/4, 3/4]


        if loop_type == "1":
            end_time = [0.5, 2, 3, 4, 6, 8]
            bar_list = [96, 12, 8, 6, 4, 2]  
        elif loop_type == "2":
            end_time = [6, 8, 3, 4, 2, 1]
            bar_list = [5, 4, 10, 8, 16, 32] 
        elif loop_type == "3":
            end_time = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
            bar_list = [32, 32, 16, 16, 8, 8]
        else:
            end_time = [3, 3, 3, 4, 4, 4]
            bar_list = [7, 7, 7, 4, 4, 4]
        ############################


        clip_w = clip.w / r_rate
        clip_h = clip.h / r_rate

        # background color shuffle
        random.shuffle(rgb_color)

        clip_list = []
        resize_list = []
        blank_list = []

        for i in range(1, 7):
            clip_list.append(clip.subclip(clip.duration * start_time[i-1], clip.duration * start_time[i-1] + end_time[i-1]))

            if i == 1:
                resize_list.append(resize(clip_list[i-1], (clip_w, clip_h)))
                blank_list.append(ColorClip((math.ceil(clip_w), math.ceil(clip_h)), color=(rgb_color[i-1]), duration=end_time[i-1]))
            else:
                resize_list.append(resize(clip_list[i-1], (clip_w / 2, clip_h / 2)))
                blank_list.append(ColorClip((math.ceil(clip_w / 2), math.ceil(clip_h / 2)), color=(rgb_color[i-1]), duration=end_time[i-1]))


        ############################
        # config
                
        if loop_type == "1":
            total_bar1 = [resize_list[0]] * 16
            total_bar1 += [resize_list[0]] * bar_list[0]
            total_bar1 += [resize_list[0]] * 16
            
            total_bar2 = [blank_list[0]] * 16
            total_bar2 += [blank_list[1], resize_list[1]] * bar_list[1]
            total_bar2 += [blank_list[0]] * 16

            total_bar3 = [blank_list[0]] * 16
            total_bar3 += [resize_list[2], blank_list[2]] * bar_list[2]
            total_bar3 += [blank_list[0]] * 16

            total_bar4 = [blank_list[0]] * 16
            total_bar4 += [blank_list[3], resize_list[3]] * bar_list[3]
            total_bar4 += [blank_list[0]] * 16

            total_bar5 = [blank_list[0]] * 16
            total_bar5 += [resize_list[4], blank_list[4]] * bar_list[4]
            total_bar5 += [blank_list[0]] * 16

            total_bar6 = [blank_list[0]] * 16
            total_bar6 += [blank_list[5], resize_list[5], blank_list[5]] * bar_list[5]
            total_bar6 += [blank_list[0]] * 16
        elif loop_type == "2":
            total_bar1 = [blank_list[0], resize_list[0]] * bar_list[0]
            total_bar2 = [blank_list[1], resize_list[1]] * bar_list[1]
            total_bar3 = [blank_list[2], resize_list[2]] * bar_list[2]
            total_bar4 = [blank_list[3], resize_list[3]] * bar_list[3]
            total_bar5 = [blank_list[4], resize_list[4]] * bar_list[4]
            total_bar6 = [blank_list[5], resize_list[5]] * bar_list[5]
        elif loop_type == "3":
            r_l1 = [blank_list[0], resize_list[0]]    
            r_l2 = [blank_list[1], resize_list[1]]
            r_l3 = [blank_list[2], resize_list[2]]    
            r_l4 = [blank_list[3], resize_list[3]]
            r_l5 = [blank_list[4], resize_list[4]]    
            r_l6 = [blank_list[5], resize_list[5]]
    
            total_bar1 = [
                random.choice(r_l1),
                random.choice(r_l1),
                random.choice(r_l1),
                random.choice(r_l1),
            ] * bar_list[0]
            total_bar2 = [
                random.choice(r_l2),
                random.choice(r_l2),
                random.choice(r_l2),
                random.choice(r_l2),
            ] * bar_list[1]
            total_bar3 = [
                random.choice(r_l3),
                random.choice(r_l3),
                random.choice(r_l3),
                random.choice(r_l3),
                random.choice(r_l3),
                random.choice(r_l3),
                random.choice(r_l3),
                random.choice(r_l3),
            ] * bar_list[2]
            total_bar4 = [
                random.choice(r_l4),
                random.choice(r_l4),
                random.choice(r_l4),
                random.choice(r_l4),
                random.choice(r_l4),
                random.choice(r_l4),
                random.choice(r_l4),
                random.choice(r_l4),
            ] * bar_list[3]
            total_bar5 = [
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
            ] * bar_list[4]
            total_bar6 = [
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
            ] * bar_list[5]
        else:
            r_l1 = [blank_list[0], resize_list[0]]    
            r_l2 = [blank_list[1], resize_list[1]]
            r_l3 = [blank_list[2], resize_list[2]]    
            r_l4 = [blank_list[3], resize_list[3]]
            r_l5 = [blank_list[4], resize_list[4]]    
            r_l6 = [blank_list[5], resize_list[5]]
    
            total_bar1 = [
                random.choice(r_l1),
                random.choice(r_l1),
                random.choice(r_l1),
            ] * bar_list[0]
            total_bar2 = [
                random.choice(r_l2),
                random.choice(r_l2),
                random.choice(r_l2),
            ] * bar_list[1]
            total_bar3 = [
                random.choice(r_l3),
                random.choice(r_l3),
                random.choice(r_l3),
            ] * bar_list[2]
            total_bar4 = [
                random.choice(r_l4),
                random.choice(r_l4),
                random.choice(r_l4),
                random.choice(r_l4),
            ] * bar_list[3]
            total_bar5 = [
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
                random.choice(r_l5),
            ] * bar_list[4]
            total_bar6 = [
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
                random.choice(r_l6),
            ] * bar_list[5]        
        ############################


        final_clip1 = concatenate_videoclips(total_bar1)
        final_clip2 = concatenate_videoclips(total_bar2)
        final_clip3 = concatenate_videoclips(total_bar3)
        final_clip4 = concatenate_videoclips(total_bar4)
        final_clip5 = concatenate_videoclips(total_bar5)
        final_clip6 = concatenate_videoclips(total_bar6)

        video = CompositeVideoClip([
            final_clip1.margin(right=math.ceil(clip_w / 2), bottom=math.ceil(clip_h / 2)),
            final_clip2.set_position((clip_w, 0)),
            final_clip3.set_position((clip_w, clip_h / 2)),
            final_clip4.set_position((0, clip_h)),
            final_clip5.set_position((clip_w / 2, clip_h)),
            final_clip6.set_position((clip_w, clip_h)),
        ])

        video.write_videofile(f"static/mp4/{video_name}.mp4", codec="libx264", audio_codec="aac")


        conn = sqlite3.connect(dbname)
        cur = conn.cursor()
        query = f"""
            INSERT INTO 
                videos(video_title, video_name, created_at)
                values("{video_title}", "{video_name}", {created_at})
        """
        cur.execute(query)
        conn.commit()
        conn.close()


        if file_type == "video/quicktime":
            os.remove(f"tmp/{video_name}.mov")
        else:
            os.remove(f"tmp/{video_name}.mp4")

        return redirect(url_for("results", id=video_name))


@app.route("/results")
def results():
    conn = sqlite3.connect(dbname)
    cur = conn.cursor()
    query = f"""
        SELECT * FROM videos WHERE video_name = ?
    """
    cur.execute(query, (request.args.get("id"),))
    video = cur.fetchone()
    conn.close()

    if video is None:
        return redirect(url_for("error"))

    return render_template("results.html", id=request.args.get("id"), video_title=video[1])


@app.route("/list")
def list():

    page = int(request.args.get('page', 1))
    next = 1

    def has_next_page(page_number, items_per_page, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM videos ORDER BY id LIMIT {num_items} OFFSET ?", (page * num_items,))
        next_page_data = cursor.fetchone()

        conn.close()

        return next_page_data is None

    if has_next_page(page, num_items, dbname):
        next = 0
    
        if table_exists('videos', dbname):
            return redirect(url_for("error"))


    try:
        if page < 0:
            return redirect(url_for("error"))
        
        conn = sqlite3.connect(dbname)
        cur = conn.cursor()
        query = f"""
            SELECT * FROM videos 
            ORDER BY created_at DESC
            LIMIT {num_items}
            OFFSET {num_items * (page - 1)}
        """
        cur.execute(query)
        videos = cur.fetchall()
        conn.close()

        if videos is None:
            return redirect(url_for("error"))

        return render_template("list.html", videos=videos, prev_page=page-1, next_page=page+1, next=next)

    except ValueError:
        return redirect(url_for("error"))
    

@app.route("/error")
def error():
    return render_template("error.html")


if __name__ == '__main__':
    app.run()