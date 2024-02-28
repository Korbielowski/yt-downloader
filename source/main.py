from flask import Flask, render_template, redirect, url_for, request, session, send_file
from pytube import YouTube, StreamQuery
from pytube.exceptions import VideoUnavailable


app = Flask(__name__)
app.secret_key = "dadadada231kj"
app.config["SESSION_PERMANENT"] = False
Vids: StreamQuery | None = None


@app.route("/")
def index():
    if not session:
        return render_template("index.html", streams_info=None, video_info=None)
    return render_template(
        "index.html",
        streams_info=session["streams_info"],
        video_info=session["video_info"],
    )


# TODO Save videos in temp folder as temporary files
@app.route("/download<int:video_id>", methods=["GET"])
def download_video(video_id):
    if Vids != None:
        return send_file(
            Vids.get_by_itag(video_id).download(output_path="../temp"),
            as_attachment=True,
        )
    return redirect(url_for("index"))


@app.route("/video", methods=["GET", "POST"])
def video():
    if request.method == "POST":
        url: str = request.form["url"]
        try:
            video = YouTube(url)
        except VideoUnavailable:
            return redirect(url_for("index"))

        # TODO: Better video length ad bitrate strings
        length: str = (
            f"{int(video.length / 3600)}:{int(video.length / 60) - int(video.length / 3600) * 60}:{(video.length % 3600) % 60}"
        )
        date: str = (
            f"{video.publish_date.year}.{video.publish_date.month}.{video.publish_date.day}"
        )

        video_info = {
            "author": video.author,
            "views": video.views,
            "length": length,
            "publish_date": date,
            "rating": video.rating,
            "description": video.description,
            "channel_id": video.channel_id,
        }

        streams_info = []
        for stream in video.streams:
            stream_info = []
            bitrate: str = (
                f"{int(stream.bitrate / 1000)}.{stream.bitrate - int(stream.bitrate / 1000) * 1000}"
            )
            stream_info.append(stream.resolution)
            stream_info.append(stream.type)
            stream_info.append(bitrate)
            stream_info.append(stream.video_codec)
            stream_info.append(stream.audio_codec)
            stream_info.append(stream.filesize_mb)
            stream_info.append(stream.itag)
            streams_info.append(stream_info)

        global Vids
        Vids = video.streams

        session["video_info"] = video_info
        session["streams_info"] = streams_info
    return redirect(url_for("index"))


@app.teardown_appcontext
def cleanup(exception):
    print("Cleanup was called when closing app")


# TODO: Try to remove global Vids variable and replace it with a better solution (Proxy, cache etc.)
