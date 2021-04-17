__version__ = '0.1.0'
import argparse
import sys
import os
import json
import multiprocessing
import logging
import itertools
from hybrid_mode0.file_utils import *

import p1204_3
from p1204_3 import *


def hyn0_predict(
    videofilename,
    model,
    device_type,
    device_resolution,
    viewing_distance,
    display_size,
    temporary_folder,
    cache_features,
    video_bitrate,
    video_width,
    video_height,
    video_framerate,
    video_codec,
    temporary_re_encoded_video_folder,
    hybrid_model_type
):
    assert(hybrid_model_type in [1,2])
    logging.info(f"videofilename = {videofilename}")
    re_encoded_video = os.path.join(temporary_re_encoded_video_folder, flat_name(get_basename(videofilename)) + ".mkv")
    logging.info(f"re_encoded_video = {re_encoded_video}")

    encoder_mapping = {
        "h264": "libx264",
        "hevc": "libx265",
        "vp9": "libvpx-vp9"
    }
    encoder = encoder_mapping.get(video_codec, "")

    if hybrid_model_type == 2:
        cmd = f"ffmpeg -nostdin -loglevel quiet -threads 4 -y -i '{videofilename}' -c:v libx265 -b:v {video_bitrate}k -vf scale='{video_width}:{video_height}' -r '{video_framerate}' -pix_fmt yuv420p -an '{re_encoded_video}' 2>/dev/null"
        # .format(videofilename=videofilename, video_bitrate=video_bitrate, video_width=video_width, video_height=video_height, video_framerate=video_framerate, re_encoded_video=re_encoded_video)

        logging.debug(f"encoding command = {cmd}")
        res = shell_call(cmd).strip()

        prediction = predict_quality(
            re_encoded_video, #videofilename,
            model,
            device_type,
            device_resolution,
            viewing_distance,
            display_size,
            temporary_folder,
            cache_features
        )
        logging.debug(prediction)

        per_sequence_transcoded = prediction["per_sequence"]
        per_second_scores = []

        # SG: is there no correction for H265 required?
        coeffs = {
            "h264": [0.90534066, 0.09309030],
            "vp9": [0.85302496, 0.69794354]
            "hevc": [1, 0]  # no change
        }
        prediction["per_sequence"] =  coeffs[video_codec][0] * prediction["per_sequence"] + coeffs[video_codec][1]

        for per_second_score in prediction["per_second"]:
            per_second_scores.append((per_second_score / per_sequence_transcoded) * prediction["per_sequence"])
        prediction["per_second"] = per_second_scores

    else:
        cmd = "ffmpeg -nostdin -loglevel quiet -threads 4 -y -i '{videofilename}' -c:v '{video_codec}' -b:v {video_bitrate}k -vf scale='{video_width}:{video_height}' -r '{video_framerate}' -pix_fmt yuv420p -an '{re_encoded_video}' 2>/dev/null".format(
        videofilename=videofilename, video_bitrate=video_bitrate, video_codec=encoder, video_width=video_width, video_height=video_height, video_framerate=video_framerate, re_encoded_video=re_encoded_video)

        logging.debug(f"encoding command = {cmd}")
        res = shell_call(cmd).strip()

        prediction = predict_quality(
            re_encoded_video, #videofilename,
            model,
            device_type,
            device_resolution,
            viewing_distance,
            display_size,
            temporary_folder,
            cache_features
        )

        logging.debug(prediction)


    # print(f"encoding command = {cmd}")
    # res = shell_call(cmd).strip()

    # prediction = predict_quality(
    #     re_encoded_video, #videofilename,
    #     model,
    #     device_type,
    #     device_resolution,
    #     viewing_distance,
    #     display_size,
    #     temporary_folder,
    #     cache_features
    # )

    os.remove(re_encoded_video)

    # return predict_quality(
    #     re_encoded_video, #videofilename,
    #     model,
    #     device_type,
    #     device_resolution,
    #     viewing_distance,
    #     display_size,
    #     temporary_folder,
    #     cache_features
    # )

    return prediction


def main(_=[]):
    # argument parsing
    parser = argparse.ArgumentParser(
        description="Hybrid no-reference mode 0 video quality model reference implementation",
        epilog="rrao, stg7 2021",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("video", type=str, nargs="+", help="input video to estimate quality")
    parser.add_argument("--result_folder", type=str, default="reports", help="folder to store video quality results")
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="model config file to be used for prediction",
    )
    parser.add_argument(
        "--hybrid_model_type",
        choice=[1,2],
        default=1,
        help="applicable input values: {1,2}; two variants: (1) uses the specific codec to re-encode the video, (2) uses HEVC to re-encode the video irrespective of the codec",
    )
    parser.add_argument("--cpu_count", type=int, default=multiprocessing.cpu_count(), help="thread/cpu count")
    parser.add_argument("--device_type", choices=DEVICE_TYPES, default="pc", help="device that is used for playout")
    parser.add_argument(
        "--device_resolution",
        choices=DEVICE_RESOLUTIONS,
        default="3840x2160",
        help="resolution of the output device (width x height)",
    )
    parser.add_argument(
        "--viewing_distance",
        choices=VIEWING_DISTANCES,
        default="1.5xH",
        help="viewing distance relative to the display height",
    )
    parser.add_argument(
        "--display_size", choices=DISPLAY_SIZES, type=float, default=55, help="display diagonal size in inches"
    )
    parser.add_argument(
        "--tmp",
        type=str,
        default="./tmp",
        help="temporary folder to store bitstream stats and other intermediate results",
    )
    parser.add_argument(
        "--tmp_reencoded",
        type=str,
        default="./tmp_reencoded",
        help="temporary folder to store re-encoded video segments",
    )
    parser.add_argument(
        "-br", "--re_encoding_bitrate",
        type=float,
        help="bitrate to re-encode the video",
    )
    parser.add_argument(
        "-vw", "--re_encoding_width",
        type=float,
        help="width to re-encode the video",
    )
    parser.add_argument(
        "-vh", "--re_encoding_height",
        type=float,
        help="height to re-encode the video",
    )
    parser.add_argument(
        "-fr", "--re_encoding_framerate",
        type=float,
        help="framerate to re-encode the video",
    )
    parser.add_argument(
        "-codec", "--re_encoding_codec",
        type=str,
        default="hevc",
        help="codec to re-encode the video",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="show debug output",
    )
    parser.add_argument(
        "-nocached_features",
        action="store_true",
        help="no caching of features",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="not print any output except errors",
    )

    a = vars(parser.parse_args())
    logging.basicConfig(level=logging.DEBUG)

    logging.info(f"handle the following videos (# {len(a['video'])}): \n  " + "\n  ".join(a["video"]))
    os.makedirs(a["tmp_reencoded"], exist_ok=True)
    params = [
        (
            video,
            a["model"],
            a["device_type"],
            a["device_resolution"],
            a["viewing_distance"],
            a["display_size"],
            a["tmp"],
            not a["nocached_features"],
            a["re_encoding_bitrate"],
            a["re_encoding_width"],
            a["re_encoding_height"],
            a["re_encoding_framerate"],
            a["re_encoding_codec"],
            a["tmp_reencoded"],
            a["hybrid_model_type"]
        )
        for video in a["video"]
    ]
    print(params)
    if a["cpu_count"] > 1:
        pool = multiprocessing.Pool(a["cpu_count"])
        results = pool.starmap(hyn0_predict, params)
    else:
        results = list(itertools.starmap(hyn0_predict, params))

    print(json.dumps(results, indent=4, sort_keys=True))
    logging.info(f"""store all results to {a["result_folder"]}""")
    os.makedirs(a["result_folder"], exist_ok=True)
    for result in results:
        if result == {} or "video_basename" not in result:
            # in case the video could not be processed, just ignore it
            continue
        reportname = os.path.join(a["result_folder"], os.path.splitext(result["video_basename"])[0] + ".json")
        json_store(reportname, result)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))