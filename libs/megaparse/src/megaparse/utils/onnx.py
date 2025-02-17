import logging
from typing import List

import onnxruntime as rt
from megaparse.configs.auto import DeviceEnum

logger = logging.getLogger("megaparse")


def get_providers(device: DeviceEnum) -> List[str]:
    prov = rt.get_available_providers()
    logger.info("Available providers: %s", prov)
    if device == DeviceEnum.CUDA:
        if "CUDAExecutionProvider" not in prov:
            raise ValueError(
                "onnxruntime can't find CUDAExecutionProvider in list of available providers"
            )
        return ["CUDAExecutionProvider"]
    elif device == DeviceEnum.COREML:
        if "CoreMLExecutionProvider" not in prov:
            raise ValueError(
                "onnxruntime can't find CoreMLExecutionProvider in list of available providers"
            )
        return ["CoreMLExecutionProvider"]
    elif device == DeviceEnum.CPU:
        return ["CPUExecutionProvider"]
    else:
        raise ValueError("device not in (CUDA,CoreML,CPU)")
