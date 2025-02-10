import logging
import warnings
from typing import List

import onnxruntime as rt
from megaparse.configs.auto import DeviceEnum

logger = logging.getLogger("megaparse")


def get_providers(device: DeviceEnum) -> List[str]:
    prov = rt.get_available_providers()
    logger.info("Available providers:", prov)
    if device == DeviceEnum.CUDA:
        # TODO: support openvino, directml etc
        if "CUDAExecutionProvider" not in prov:
            raise ValueError(
                "onnxruntime can't find CUDAExecutionProvider in list of available providers"
            )
        return ["TensorrtExecutionProvider", "CUDAExecutionProvider"]
    elif device == DeviceEnum.COREML:
        if "CoreMLExecutionProvider" not in prov:
            raise ValueError(
                "onnxruntime can't find CoreMLExecutionProvider in list of available providers"
            )
        return ["CoreMLExecutionProvider"]
    elif device == DeviceEnum.CPU:
        return ["CPUExecutionProvider"]
    else:
        warnings.warn(
            "Device not supported, using CPU",
            UserWarning,
            stacklevel=2,
        )
        return ["CPUExecutionProvider"]
