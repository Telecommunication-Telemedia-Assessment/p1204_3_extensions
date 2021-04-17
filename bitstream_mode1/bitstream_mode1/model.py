#!/usr/bin/env python3
"""
style: black -l 140 model.py
"""
import logging
import json
import os
import datetime

from bitstream_mode1 import __version__
from bitstream_mode1.utils import assert_file
from bitstream_mode1.utils import assert_msg
from bitstream_mode1.utils import ffprobe
from bitstream_mode1.utils import json_load
from bitstream_mode1.modelutils import map_to_45
from bitstream_mode1.modelutils import map_to_5
from bitstream_mode1.modelutils import r_from_mos
from bitstream_mode1.modelutils import mos_from_r
from bitstream_mode1.modelutils import load_serialized
from bitstream_mode1.modelutils import binarize_column
from bitstream_mode1.modelutils import load_dict_values
from bitstream_mode1.modelutils import per_sample_interval_function
from bitstream_mode1.generic import *

import bitstream_mode1.features as features
from bitstream_mode1.features import *

from bitstream_mode1.extract_video_frame_info import *


class BitstreamMode1:
    """
    bitstram mode 1 short term video quality prediction model
    """

    def __init__(self):
        self.display_res = 3840 * 2160

    def _calculate(self, prediction_features, params, display_res, device_type):

        def mos_q_baseline_pc(features, a, b, c, d):
            print("a = {}, b = {}, c = {}, d = {}".format(a,b,c,d))
            quant = features["quant"]
            mos_q = a + b * np.exp(c * quant + d)
            mos_q = np.clip(mos_q,1,5)
            mos_q = np.vectorize(r_from_mos)(mos_q)
            cod_deg = 100 - mos_q
            cod_deg = np.clip(cod_deg,0,100)
            return cod_deg


        prediction_features = prediction_features.copy()

        prediction_features = load_dict_values(prediction_features, "IFrameRatio")
        # print(prediction_features.columns)

        # change this to different things for mobile and pc
        def predqp_pc(row):
            if row["Codec"] not in ["h264", "hevc", "vp9"]:
                return -1
            if row["Codec"] == "h264":
                e = -5.45370021
                d =  0.24788992
                c =  5.78207198
                b = -7.39512320
                a =  28.4333174
            if row["Codec"] == "hevc":
                e = -2.28896532
                d = -0.89995975
                c =  5.15729271
                b = -6.52974529
                a =  22.3936569
            if row["Codec"] == "vp9":
                e = -18.7808971
                d = -10.2195346
                c =  40.6831660
                b = -51.1209683
                a =  92.1245351
            pred_qp = a + b*np.log(row["IFrameRatio_mean_noniframesize"]) + c*np.log(row["Resolution"]) + d*np.log(row["Framerate"]) + e*np.log(row["IFrameRatio_iframe_noniframe_ratio_mean"])
            return pred_qp

        def predqp_mobile(row):
            if row["Codec"] not in ["h264", "hevc", "vp9"]:
                return -1
            if row["Codec"] == "h264":
                e = -6.51258585
                d = -0.86271189
                c =  6.11739209
                b = -7.40096124
                a =  30.6150034
            if row["Codec"] == "hevc":
                e = -3.83762247
                d = -3.04775031
                c =  5.77213226
                b = -7.05771310
                a =  29.6766107
            if row["Codec"] == "vp9":
                e =  -24.9768715
                d =   1.83157999
                c =   34.3946143
                b =  -49.8642457
                a =   145.132249
            pred_qp = a + b*np.log(row["IFrameRatio_mean_noniframesize"]) + c*np.log(row["Resolution"]) + d*np.log(row["Framerate"]) + e*np.log(row["IFrameRatio_iframe_noniframe_ratio_mean"])
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


        cod_deg = sum([prediction_features[c] * mos_q_baseline_pc(prediction_features, params[c + "_a"], params[c + "_b"],
                                                    params[c + "_c"], params[c + "_d"]) for c in codecs])

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

        print("x = {}, y = {}, z = {}, k = {}".format(x,y,z,k))
        print("quant = {}".format(prediction_features["quant"]))
        print("display_res = {}".format(display_res))
        resolution = x * np.log(y * (prediction_features["Resolution"]/display_res))
        resolution = np.clip(resolution,0,100)

        framerate = z * np.log(k * prediction_features["Framerate"]/60)
        framerate = np.clip(framerate,0,100)

        pred = 100 - (cod_deg + resolution + framerate)
        pred = np.vectorize(mos_from_r)(pred)
        pred = np.clip(pred,1,5)
        predicted_score = np.vectorize(map_to_5)(pred)
        initial_predicted_score = np.vectorize(map_to_5)(pred)
        prediction_features["predicted_mos_mode1_baseline"] = initial_predicted_score

        result = {
            "final_pred": predicted_score,
            "debug": {
                "baseline": prediction_features["predicted_mos_mode1_baseline"],
                "coding_deg": cod_deg,
                "upscaling_deg": resolution,
                "temporal_deg": framerate,
                # "rf_pred": prediction_features_rf["rf_pred"],
                # "rf_pred": prediction_features["rf_pred"],
            },
            # "features": feature_values

        }
        return result

    def valid_for(self):
        return {
            "mode": [1],
            "version": 1
        }

    def features_used(self):
        return [
            features.Bitrate,
            features.Framerate,
            features.Resolution,
            features.Codec,
            features.IFrameRatio
        ]


    def predict_quality(
        self,
        videofilename,
        model_config_filename,
        device_type="pc",
        device_resolution="3840x2160",
        viewing_distance="1.5xH",
        display_size=55,
        temporary_folder="tmp",
        cache_features=True
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

        os.makedirs(temporary_folder, exist_ok=True)

        feature_cache = os.path.join(
            temporary_folder, os.path.splitext(os.path.basename(videofilename))[0] + "_feat.pkl"
        )
        logging.info(f"use feature cache file {feature_cache}")
        if not os.path.isfile(feature_cache):
            # run framesize info extraction
            framesizeinfo_result_file = ffprobe_frame_info(videofilename, temporary_folder)
            if framesizeinfo_result_file == "":
                logging.error(f"no framsize information file for {videofilename}")
                return {}

            # calculate features
            features = pd.DataFrame(
                [extract_features(videofilename, self.features_used(), ffprobe_result, framesizeinfo_result_file)]
            )
            features.to_pickle(feature_cache)
        else:
            logging.info("features are already cached, extraction skipped")
            features = pd.read_pickle(feature_cache)

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
                "coding_deg": float(per_sequence["debug"]["coding_deg"]),
                "upscaling_deg": float(per_sequence["debug"]["upscaling_deg"]),
                "temporal_deg": float(per_sequence["debug"]["temporal_deg"]),
            },
            "date": str(datetime.datetime.now()),
            "model": "bitstream_mode1",
            "version": __version__,
        }
