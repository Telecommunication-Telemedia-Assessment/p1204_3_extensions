#!/usr/bin/env python3
import argparse
import sys
import os
import json
import multiprocessing
import logging
import itertools

from .file_utils import *
from . import __version__

import p1204_3
from p1204_3 import predict_quality as p1204_3_predict_quality
from p1204_3.generic import *

from p1204_3.utils import *


def re_encode_video(videofilename, encoder, video_bitrate, video_width, video_height, video_framerate, re_encoded_video):
    if os.path.isfile(re_encoded_video):
        logging.warn(f"{videofilename} has been alreadyy reencoded with these settings, see {re_encoded_video}; please check, encoding settings may vary, however the encoding step will be skipped")
        return
    cmd = " ".join(f"""
        ffmpeg -nostdin -loglevel quiet -threads 4 -y -i
        '{videofilename}'
        -c:v {encoder}
        -b:v {video_bitrate}
        -vf scale="{video_width}:{video_height}"
        -r {video_framerate}
        -pix_fmt yuv420p
        -an "{re_encoded_video}" 2>/dev/null
    """.split())

    logging.debug(f"encoding command = {cmd}")
    res = shell_call(cmd).strip()
    return res


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
    cache_reencodes,
    hybrid_model_type
):
    logging.info(f"handle videofilename = {videofilename}")

    assert_msg(hybrid_model_type in [1,2], f"hybrid_model_type={hybrid_model_type} not valid, must be in [1,2]")
    assert_file(videofilename, f"videofilename={videofilename} does not exist")
    assert_msg(not(hybrid_model_type == 1 and video_codec is None), f"for hybrid_model_type 1 you need to specify a vidoe_codec")

    encoder_mapping = {
        "h264": "libx264",
        "hevc": "libx265",
        "h265": "libx265",
        "vp9": "libvpx-vp9"
    }

    # hybrid_model_type == 2 uses h265 as target video codec
    encoder = "libx265" if hybrid_model_type == 2 else encoder_mapping[video_codec]

    assert_msg(encoder is not None, f"video_codec={video_codec} not yet supported, use hybrid_model_type = 2")

    encoding_params = "_".join(map(str, [
            video_bitrate,
            video_width,
            video_height,
            video_framerate,
            encoder
        ])
    )

    re_encoded_video = os.path.join(
        temporary_re_encoded_video_folder,
        flat_name(get_basename(videofilename)) + "_settings_" +  encoding_params
        + ".mkv"
    )
    logging.info(f"re_encoded_video = {re_encoded_video}")

    re_encode_video(
        videofilename,
        encoder,
        video_bitrate,
        video_width,
        video_height,
        video_framerate,
        re_encoded_video
    )

    logging.info(f"predict quality of {re_encoded_video}")
    prediction = p1204_3_predict_quality(
        re_encoded_video,
        model,
        device_type,
        device_resolution,
        viewing_distance,
        display_size,
        temporary_folder,
        cache_features
    )

    prediction["model"] = "hybrid_type_" + str(hybrid_model_type)
    prediction["version"] = __version__
    prediction["video_basename"] = os.path.basename(videofilename) + encoding_params
    prediction["video_full_path"] = videofilename

    prediction["hybrid_encoding_params"] = {
        "video_bitrate": video_bitrate,
        "video_width": video_width,
        "video_height": video_height,
        "video_framerate": video_framerate,
        "encoder": encoder
    }

    logging.debug(prediction)

    if not cache_reencodes:
        os.remove(re_encoded_video)

    if hybrid_model_type == 1:
        # for hybrid_model_type 1 no correction is performed
        # SG: todo: a correction may be required, e.g.
        # poetry run hybrid_mode0 ../test_videos/BlackDesert_30_1920x1080_60_2000_h264_nvenc.mp4  -br 100k -vw 1024 -vh 120 -fr 60  -d --cpu_count 1 -cache_reencodes --hybrid_model_type 1 -codec h264
        # returns 3.408 (overall quality), and the video is really bad
        # while the mode 2 variant returns 1.05
        return prediction

    per_sequence_transcoded = prediction["per_sequence"]
    per_second_scores = []

    codec_specific_coeffs = {
        "h264": [0.90534066, 0.09309030],
        "vp9": [0.85302496, 0.69794354]
    }

    if video_codec not in codec_specific_coeffs:
        logging.warn(f"for your current video codec {video_codec} no correction of the final scores is performed")

    if video_codec in codec_specific_coeffs:
        prediction["per_sequence"] =  codec_specific_coeffs[video_codec][0] * prediction["per_sequence"] + codec_specific_coeffs[video_codec][1]

    for per_second_score in prediction["per_second"]:
        per_second_scores.append((per_second_score / per_sequence_transcoded) * prediction["per_sequence"])

    prediction["per_second"] = per_second_scores

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
        choices=[1, 2],
        type=int,
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
        default=DEFAULT_VIEWING_DISTANCE,
        help="viewing distance relative to the display height",
    )
    parser.add_argument(
        "--display_size", choices=DISPLAY_SIZES, type=float, default=DEFAULT_DISPLAY_SIZE, help="display diagonal size in inches"
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
        help="bitrate to re-encode the video; supports ffmpeg style bitrate, e.g. 100k, 5M",
        required=True
    )
    parser.add_argument(
        "-vw", "--re_encoding_width",
        type=int,
        help="width to re-encode the video",
        required=True
    )
    parser.add_argument(
        "-vh", "--re_encoding_height",
        type=int,
        help="height to re-encode the video",
        required=True
    )
    parser.add_argument(
        "-fr", "--re_encoding_framerate",
        type=float,
        help="framerate to re-encode the video",
        required=True
    )
    parser.add_argument(
        "-codec", "--re_encoding_codec",
        type=str,
        help="codec to re-encode the video, if not specific mode will be set to 1"
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
        "-cache_reencodes",
        action="store_true",
        help="caching reencoded videos",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="not print any output except errors",
    )

    a = vars(parser.parse_args())

    if a["debug"]:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("debug output enabled")
    elif a["quiet"]:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)

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
            a["cache_reencodes"],
            a["hybrid_model_type"]
        )
        for video in a["video"]
    ]
    logging.debug(params)
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