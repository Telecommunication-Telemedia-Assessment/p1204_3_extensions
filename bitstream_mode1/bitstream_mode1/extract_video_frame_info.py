#!/usr/bin/env python3
import os
import sys
import logging
import shutil
import subprocess
import json
import pandas as pd
from bitstream_mode1.utils import shell_call

def ffprobe_frame_info(video_segment_file, output_dir_full_path, skipexisting=True):  #(filename):
    """ run ffprobe to get some information of a given video file
    """
    if shutil.which("ffprobe") is None:
        raise Exception("you need to have ffprobe installed, please read README.md.")

    if not os.path.isfile(video_segment_file):
        raise Exception("{} is not a valid file".format(filename))

    # ffprobe -loglevel error -select_streams v -show_frames -show_entries
    # frame=pkt_pts_time,pkt_dts_time,pkt_duration_time,pkt_size,pict_type -of json
    # videoSegments/SRC1_HRC003_Q3_0-20.mkv >> frame_information/SRC1_HRC003_Q3_0-20.json

    logging.info("run frameize extraction for {}".format(video_segment_file))
    report_file_name = os.path.join(
        output_dir_full_path,
        os.path.splitext(os.path.basename(video_segment_file))[0] + ".json"
    )
    if skipexisting and os.path.isfile(report_file_name):
        return report_file_name

    cmd = "ffprobe -loglevel error -select_streams v -show_frames -show_entries frame=pkt_pts_time,pkt_dts_time,pkt_duration_time,pkt_size,pict_type -of json '{filename}' >>{report_file_name}".format(
        filename=video_segment_file, report_file_name=report_file_name
    )

    # print(cmd)
    res = shell_call(cmd).strip()

    if os.path.getsize(report_file_name) == 0:
        raise Exception("{} is somehow not valid, so ffprobe could not extract anything".format(filename))
        return ""
    return report_file_name

    """
    needed = {
        "pkt_size": "unknown",
        "pict_type": "unknown",
        "iframesizes": "unknown",
        "noni_framesizes": "unknown"
    }


    # frame_info_file = filename + ".json"
    frame_info_list = []
    with open(report_file_name) as f:
        val = json.load(f)

        for x in val["frames"]:
            frame_info_list.append(x)

        df = pd.DataFrame(frame_info_list)
        df = df[["pict_type", "pkt_size"]]
        df["pkt_size"] = pd.to_numeric(df["pkt_size"])

        df_i = df[df["pict_type"] == "I"]
        df_non_i = df[df["pict_type"] != "I"]
    
    needed["iframesizes"] = df_i["pkt_size"]
    needed["noni_framesizes"] = df_non_i["pkt_size"]
    return needed
    """