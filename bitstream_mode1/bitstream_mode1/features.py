#!/usr/bin/env python3
import logging
import json

import numpy as np
import pandas as pd
import scipy.stats

from bitstream_mode1.utils import assert_msg
from bitstream_mode1.utils import file_open


def extract_features(videofilename, used_features, ffprobe_result, framesizeinfo_result_file):
    """ extract all specified features for a given video file """
    features = {}
    pvs = PVS(videofilename, ffprobe_result, framesizeinfo_result_file)
    for f in used_features:
        features[str(f.__name__)] = f().calculate(pvs)
    features["duration"] = Duration().calculate(pvs)
    features["videofilename"] = videofilename
    return features


class PVS:
    """ Wrapper to access ffprobe / framesize statistics internally """

    def __init__(self, videofilename, ffprobe_result, framesizeinfo_result_file):
        self._videofilename = videofilename
        self._ffprobe_result = ffprobe_result
        self._framesizeinfo_result_file = framesizeinfo_result_file

    def get_frames_from_framesize_info(self):
        frame_info_list = []
        framesize_info_stats = {}
        with file_open(self._framesizeinfo_result_file) as framestat:
            # framesize_info_stats = json.load(framestat)
            # print(framesize_info_stats)
            val = json.load(framestat)

            frame_info_list = [x for x in val["frames"]]

            df = pd.DataFrame(frame_info_list)
            df = df[["pict_type", "pkt_size"]]
            df["pkt_size"] = pd.to_numeric(df["pkt_size"])

            df_i = df[df["pict_type"] == "I"]
            df_non_i = df[df["pict_type"] != "I"]

        framesize_info_stats["iframesizes"] = df_i["pkt_size"]
        framesize_info_stats["noni_framesizes"] = df_non_i["pkt_size"]
        # return needed
        return framesize_info_stats

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

class IframeSizes:
    """
    List of I frame sizes
    """
    def calculate(self, processed_video_sequence):
        frames = processed_video_sequence.get_frames_from_framesize_info()
        return [frame.pkt_size for frame in frames if frame.pict_type == "I"]

    def valid_for(self):
        return {
            "mode": [1, 2, 3],
            "version": 1
        }

class NonIframeSizes:
    """
    List of Non-I frame sizes
    """
    def calculate(self, processed_video_sequence):
        frames = processed_video_sequence.get_frames_from_framesize_info()
        return [frame.pkt_size for frame in frames if frame.pict_type != "I"]

    def valid_for(self):
        return {
            "mode": [1, 2, 3],
            "version": 1
        }

class IFrameRatio:
    """
    iframe_sizes / non_iframe_sizes based features
    """
    def calculate(self, processed_video_sequence):
        framesize_info_stats = processed_video_sequence.get_frames_from_framesize_info()
        iframesizes = framesize_info_stats["iframesizes"] #IframeSizes().calculate(processed_video_sequence)
        non_iframesizes = framesize_info_stats["noni_framesizes"] #NonIframeSizes().calculate(processed_video_sequence)
        result = {}
        result["ratio_mean"] = np.mean(iframesizes) / ((np.mean(non_iframesizes) + np.mean(iframesizes)))
        result["ratio_median"] = np.median(iframesizes) / ((np.median(non_iframesizes) + np.median(iframesizes)))
        result["ratio_std"] = np.std(iframesizes) / ((np.std(non_iframesizes) + np.std(iframesizes)))
        all_sizes = np.array(iframesizes + non_iframesizes)
        result["norm_std_all"] = np.std(all_sizes / all_sizes.max())
        result["norm_mean_all"] = np.mean(all_sizes / all_sizes.max())
        result["iframe_noniframe_ratio_mean"] = np.mean(iframesizes) / np.mean(non_iframesizes)
        result["iframe_noniframe_ratio_median"] = np.median(iframesizes) / np.median(non_iframesizes)
        result["iframe_noniframe_ratio_std"] = np.std(iframesizes) / np.std(non_iframesizes)
        result["mean_iframesize"] = np.mean(iframesizes)
        result["median_iframesize"] = np.median(iframesizes)
        # result["max_iframesize"] = np.amax(iframesizes)
        # result["min_iframesize"] = np.min(iframesizes, axis=0)
        result["std_iframesize"] = np.std(iframesizes)
        result["mean_noniframesize"] = np.mean(non_iframesizes)
        result["median_noniframesize"] = np.median(non_iframesizes)
        result["std_noniframesize"] = np.std(non_iframesizes)
        # result["max_noniframesize"] = np.max(non_iframesizes)
        # result["min_noniframesize"] = np.min(non_iframesizes)

        result["kurtosis_iframesize"] = float(scipy.stats.kurtosis(iframesizes))
        result["iqr_iframesize"] = float(scipy.stats.iqr(iframesizes))

        result["kurtosis_noniframesize"] = float(scipy.stats.kurtosis(non_iframesizes))
        result["iqr_noniframesize"] = float(scipy.stats.iqr(non_iframesizes))

        for i in range(11):
            percentile = round(10 * i, 1)
            result["{}_percentile_iframesize".format(percentile)] = np.percentile(iframesizes, percentile, axis=0)

        for i in range(11):
            percentile = round(10 * i, 1)
            result["{}_percentile_noniframesize".format(percentile)] = np.percentile(non_iframesizes, percentile, axis=0)

        return result

    def valid_for(self):
        return {
            "mode": [1, 2, 3],
            "version": 1
        }

