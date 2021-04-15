#!/usr/bin/env python3
import logging
import json

import numpy as np
import pandas as pd
import scipy.stats

from bitstream_mode0.utils import assert_msg
from bitstream_mode0.utils import file_open

def extract_features(videofilename, used_features, ffprobe_result):#, bitstream_parser_result_file):
    """ extract all specified features for a given video file """
    features = {}
    pvs = PVS(videofilename, ffprobe_result)#, bitstream_parser_result_file)
    for f in used_features:
        features[str(f.__name__)] = f().calculate(pvs)
    features["duration"] = Duration().calculate(pvs)
    features["videofilename"] = videofilename
    return features


class PVS:
    """ Wrapper to access ffprobe / bitstream statistics internally """

    def __init__(self, videofilename, ffprobe_result):#, bitstream_parser_result_file):
        self._videofilename = videofilename
        self._ffprobe_result = ffprobe_result
        # self._bitstream_parser_result_file = bitstream_parser_result_file

    def __str__(self):
        return self._videofilename


class Bitrate:
    """
    Average video bitrate
    """

    def calculate(self, processed_video_sequence):
        bitrate = processed_video_sequence._ffprobe_result["bitrate"]
        return float(bitrate) / 1024


class Framerate:
    """
    Video framerate
    """

    def calculate(self, processed_video_sequence):
        fps = processed_video_sequence._ffprobe_result["avg_frame_rate"]
        if fps != "unknown":
            return float(fps)
        return 60.0


class Resolution:
    """
    Resolution in pixels (width * height)
    """

    def calculate(self, processed_video_sequence):
        height = processed_video_sequence._ffprobe_result["height"]
        width = processed_video_sequence._ffprobe_result["width"]
        return width * height


class Codec:
    """
    Video codec used, either h264, hevc, vp9.
    """

    def calculate(self, processed_video_sequence):
        codec = processed_video_sequence._ffprobe_result["codec"]
        return codec


class Duration:
    """
    Video duration in seconds.
    """

    def calculate(self, processed_video_sequence):
        duration = processed_video_sequence._ffprobe_result["duration"]
        return float(duration)
