#!/usr/bin/env python3
"""
style: black -l 140 model.py
"""
import logging
import json
import os
import datetime

from bitstream_mode0 import __version__
from bitstream_mode0.utils import assert_file
from bitstream_mode0.utils import assert_msg
from bitstream_mode0.utils import ffprobe
from bitstream_mode0.utils import json_load
from bitstream_mode0.modelutils import map_to_45
from bitstream_mode0.modelutils import map_to_5
from bitstream_mode0.modelutils import r_from_mos
from bitstream_mode0.modelutils import mos_from_r
from bitstream_mode0.modelutils import load_serialized
from bitstream_mode0.modelutils import binarize_column
from bitstream_mode0.modelutils import load_dict_values
from bitstream_mode0.modelutils import per_sample_interval_function
from bitstream_mode0.generic import *

import bitstream_mode0.features as features
from bitstream_mode0.features import *


class BitstreamMode0:
    """
    bistream mode 0  short term video quality prediction model
    """

    def __init__(self):
        self.display_res = 3840 * 2160

    def _calculate(self, prediction_features, params, display_res, device_type):
        def mos_q_baseline_pc(features, a, b, c, d):
            print("a = {}, b = {}, c = {}, d = {}".format(a, b, c, d))
            quant = features["quant"]
            mos_q = a + b * np.exp(c * quant + d)
            mos_q = np.clip(mos_q, 1, 5)
            mos_q = np.vectorize(r_from_mos)(mos_q)
            cod_deg = 100 - mos_q
            cod_deg = np.clip(cod_deg, 0, 100)
            return cod_deg

        prediction_features = prediction_features.copy()

        print(params)
        # SG: shouldn't all these coeffs be part of the model.json file?, if not what values are then in this json file?
        #   in theory depending on the model and device all these coeffs should be part of params
        #   but it doesnt look like this
        # same confusion with mode 1

        # SG: there seems to be also something too much with these files
        # ./models/bitstream_mode0/config.json  <- has mobile and PC and is used..
        # ./models/bitstream_mode0/mode0baseline_mobile_final_coeff.json
        # ./models/bitstream_mode0/mode0baseline_pc_final_coeff.json

        # change this to different things for mobile and pc
        def predqp_pc(row):
            if row["Codec"] not in ["h264", "hevc", "vp9"]:
                return -1
            if row["Codec"] == "h264":
                d = 5.62309933
                c = 4.19647182
                b = -5.35863448
                a = -5.72843619
            if row["Codec"] == "hevc":
                d = 4.08694769
                c = 4.82981247
                b = -6.02561845
                a = -7.68665264

            if row["Codec"] == "vp9":
                d = 27.5875919
                c = 37.5395453
                b = -46.5290494
                a = -140.838395
            pred_qp = a + b * np.log(row["Bitrate"]) + c * np.log(row["Resolution"]) + d * np.log(row["Framerate"])
            return pred_qp

        def predqp_mobile(row):
            if row["Codec"] not in ["h264", "hevc", "vp9"]:
                return -1
            if row["Codec"] == "h264":
                d = 3.01147460
                c = 4.37840851
                b = -4.92630532
                a = -1.46439015
            if row["Codec"] == "hevc":
                d = 2.34100646
                c = 4.76721523
                b = -5.86551697
                a = -1.65354441
            if row["Codec"] == "vp9":
                d = 30.8075359
                c = 28.7095166
                b = -41.0775277
                a = -65.7419925
            pred_qp = a + b * np.log(row["Bitrate"]) + c * np.log(row["Resolution"]) + d * np.log(row["Framerate"])
            return pred_qp

        if device_type.lower() in ["pc", "tv"]:
            prediction_features["pred_qp"] = prediction_features.apply(predqp_pc, axis=1)
        else:
            prediction_features["pred_qp"] = prediction_features.apply(predqp_mobile, axis=1)

        def norm_qp(row):
            if row["Codec"] == "h264":
                return row["pred_qp"] / 63
            if row["Codec"] == "hevc":
                return row["pred_qp"] / 63
            if row["Codec"] == "vp9":
                return row["pred_qp"] / 255
            return -1

        prediction_features["quant"] = prediction_features.apply(norm_qp, axis=1)

        prediction_features = binarize_column(prediction_features, "Codec")

        codecs = prediction_features["Codec"].unique()

        cod_deg = sum(
            [
                prediction_features[c]
                * mos_q_baseline_pc(prediction_features, params[c + "_a"], params[c + "_b"], params[c + "_c"], params[c + "_d"])
                for c in codecs
            ]
        )

        if device_type.lower() in ["pc", "tv"]:
            x = -12.8292
            y = 2.4358
            z = -41.0545
            k = 3.7547
        else:
            x = -10.4174
            y = 2.2679
            z = -57.1618
            k = 3.5766

        print("x = {}, y = {}, z = {}, k = {}".format(x, y, z, k))
        print("quant = {}".format(prediction_features["quant"]))
        print("display_res = {}".format(display_res))
        resolution = x * np.log(y * (prediction_features["Resolution"] / display_res))
        resolution = np.clip(resolution, 0, 100)

        framerate = z * np.log(k * prediction_features["Framerate"] / 60)
        framerate = np.clip(framerate, 0, 100)

        pred = 100 - (cod_deg + resolution + framerate)
        pred = np.vectorize(mos_from_r)(pred)
        pred = np.clip(pred, 1, 5)
        # predicted_score = np.vectorize(map_to_5)(pred)
        initial_predicted_score = np.vectorize(map_to_5)(pred)

        return {
            "final_pred": initial_predicted_score,
            "coding_deg": cod_deg,
            "upscaling_deg": resolution,
            "temporal_deg": framerate,
        }
        # return predicted_score

    def features_used(self):
        return [features.Bitrate, features.Framerate, features.Resolution, features.Codec]

    def predict_quality(
        self,
        videofilename,
        model_config_filename,
        device_type="pc",
        device_resolution="3840x2160",
        viewing_distance="1.5xH",
        display_size=55,
        temporary_folder="tmp",
    ):

        assert_file(videofilename, f"{videofilename} does not exist, please check")
        assert_file(model_config_filename, f"{model_config_filename} does not exist, please check")

        device_type = device_type.lower()
        assert_msg(
            device_type in DEVICE_TYPES,
            f"specified device_type '{device_type}' is not supported, only {DEVICE_TYPES} possible",
        )
        assert_msg(
            device_resolution in DEVICE_RESOLUTIONS,
            f"specified device_resolution '{device_resolution}' is not supported, only {DEVICE_RESOLUTIONS} possible",
        )
        assert_msg(
            viewing_distance in VIEWING_DISTANCES,
            f"specified viewing_distance '{viewing_distance}' is not supported, only {VIEWING_DISTANCES} possible",
        )
        assert_msg(
            display_size in DISPLAY_SIZES,
            f"specified display_size '{display_size}' is not supported, only {DISPLAY_SIZES} possible",
        )

        ffprobe_result = ffprobe(videofilename)
        assert_msg(
            ffprobe_result["codec"] in CODECS_SUPPORTED,
            f"your video codec is not supported by the model: {ffprobe_result['codec']}",
        )

        model_config = json_load(model_config_filename)

        device_type = "pc" if device_type in ["pc", "tv"] else "mobile"

        # select only the required config for the device type
        model_config = model_config[device_type]

        # assume the RF model part is locally stored in the path of model_config_filename
        # rf_model = os.path.join(os.path.dirname(model_config_filename), model_config["rf"])

        # load parametetric model coefficients
        model_coefficients = model_config["params"]

        display_res = float(device_resolution.split("x")[0]) * float(device_resolution.split("x")[1])

        self.display_res = display_res

        # calculate features
        features = pd.DataFrame([extract_features(videofilename, self.features_used(), ffprobe_result)])

        logging.info("features extracted")

        # per_sequence = self._calculate(features, model_coefficients, rf_model, display_res, device_type)
        per_sequence = self._calculate(features, model_coefficients, display_res, device_type)

        per_second = per_sample_interval_function(per_sequence["final_pred"], features)
        return {
            "video_full_path": videofilename,
            "video_basename": os.path.basename(videofilename),
            "per_second": [float(x) for x in per_second],
            "per_sequence": float(per_sequence["final_pred"]),
            "debug": {
                "coding_deg": float(per_sequence["coding_deg"]),
                "upscaling_deg": float(per_sequence["upscaling_deg"]),
                "temporal_deg": float(per_sequence["temporal_deg"]),
            },
            "date": str(datetime.datetime.now()),
            "model": "bitstream_mode0",
            "version": __version__,
        }
